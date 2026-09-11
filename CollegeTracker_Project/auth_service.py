"""
Authentication and session management service for College Tracker.
Provides dual-mode authentication:
1. Firebase Cloud Authentication (REST API via Identity Toolkit)
2. Offline-first Local SQLite Authentication (SHA-256 Salted Hashing)
"""
import sqlite3
import requests
from typing import Optional, Tuple, Dict, Any
from database import get_connection, hash_password
from models import User
import config


class AuthService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self._current_user: Optional[User] = None
        self.firebase_enabled = config.FIREBASE_CONFIG.get("enabled", False)
        self.firebase_api_key = config.FIREBASE_CONFIG.get("api_key", "")
        self.firebase_auth_endpoint = config.FIREBASE_CONFIG.get("auth_endpoint", "")
        self.firebase_signup_endpoint = config.FIREBASE_CONFIG.get("signup_endpoint", "")

    @property
    def current_user(self) -> Optional[User]:
        return self._current_user

    def set_firebase_config(self, enabled: bool, api_key: str, project_id: str = "") -> None:
        """Update runtime Firebase configuration."""
        self.firebase_enabled = enabled
        self.firebase_api_key = api_key
        config.FIREBASE_CONFIG["enabled"] = enabled
        config.FIREBASE_CONFIG["api_key"] = api_key
        if project_id:
            config.FIREBASE_CONFIG["project_id"] = project_id

    def authenticate_firebase(self, email: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Authenticate against Google Firebase Authentication REST API.
        Endpoint: https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=[API_KEY]
        """
        if not self.firebase_api_key:
            return False, None, "Firebase Web API Key is not configured."

        url = f"{self.firebase_auth_endpoint}?key={self.firebase_api_key}"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }

        try:
            response = requests.post(url, json=payload, timeout=6)
            data = response.json()

            if response.status_code == 200 and "idToken" in data:
                return True, data, "Firebase authentication successful."
            else:
                error_data = data.get("error", {})
                error_msg = error_data.get("message", "Authentication failed.")
                if "EMAIL_NOT_FOUND" in error_msg or "INVALID_PASSWORD" in error_msg or "INVALID_LOGIN_CREDENTIALS" in error_msg:
                    return False, None, "Invalid Firebase email or password."
                elif "USER_DISABLED" in error_msg:
                    return False, None, "This user account has been disabled in Firebase."
                return False, None, f"Firebase Auth error: {error_msg}"
        except requests.exceptions.RequestException as e:
            return False, None, f"Firebase network timeout/offline: {str(e)}"

    def register_firebase(self, email: str, password: str, display_name: Optional[str] = None) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Register a new user in Firebase Authentication.
        Endpoint: https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=[API_KEY]
        """
        if not self.firebase_api_key:
            return False, None, "Firebase Web API Key is not configured."

        url = f"{self.firebase_signup_endpoint}?key={self.firebase_api_key}"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        if display_name:
            payload["displayName"] = display_name

        try:
            response = requests.post(url, json=payload, timeout=6)
            data = response.json()
            if response.status_code == 200:
                return True, data, "User registered in Firebase."
            else:
                error_msg = data.get("error", {}).get("message", "Registration failed.")
                return False, None, f"Firebase error: {error_msg}"
        except requests.exceptions.RequestException as e:
            return False, None, f"Firebase network error: {str(e)}"

    def authenticate(self, identifier: str, password: str, role: str) -> Tuple[bool, Optional[User], str]:
        """
        Authenticate a user by username or email, password, and role.
        Tries Firebase Auth when configured/online, and falls back to local SQLite credentials.
        """
        clean_id = identifier.strip() if identifier else ""
        clean_pw = password.strip() if password else ""
        clean_role = role.strip() if role else ""

        if not clean_id or not clean_pw or not clean_role:
            return False, None, "Please fill in all login fields."

        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        try:
            # Locate user in local SQLite by username or email
            cursor.execute("""
                SELECT * FROM users 
                WHERE username = ? OR email = ?;
            """, (clean_id, clean_id))
            row = cursor.fetchone()

            if not row:
                return False, None, "Invalid username or password."

            # Check role match
            stored_role = row["role"]
            if stored_role != clean_role:
                return False, None, f"Access denied: Selected role '{clean_role}' does not match account role '{stored_role}'."

            user_email = row["email"] if ("email" in row.keys() and row["email"]) else f"{row['username']}@college.edu"

            # 1. If Firebase Auth is enabled, try Firebase cloud verification
            if self.firebase_enabled and self.firebase_api_key:
                fb_ok, fb_data, fb_msg = self.authenticate_firebase(user_email, clean_pw)
                if fb_ok and fb_data:
                    fb_uid = fb_data.get("localId")
                    if fb_uid and "firebase_uid" in row.keys() and row["firebase_uid"] != fb_uid:
                        cursor.execute("UPDATE users SET firebase_uid = ? WHERE id = ?;", (fb_uid, row["id"]))
                        conn.commit()

                    user = User(
                        id=row["id"],
                        name=row["name"],
                        username=row["username"],
                        password_hash=row["password_hash"],
                        role=row["role"],
                        email=row["email"] if "email" in row.keys() else None,
                        semester=row["semester"] if "semester" in row.keys() else None,
                        division=row["division"] if "division" in row.keys() else None,
                        created_at=row["created_at"] if "created_at" in row.keys() else None
                    )
                    self._current_user = user
                    return True, user, "Login successful via Firebase Authentication 🔒."
                else:
                    if "Invalid Firebase" in fb_msg:
                        return False, None, fb_msg

            # 2. Local SQLite Authentication (Offline-first SHA-256 hash)
            stored_hash = row["password_hash"]
            entered_hash = hash_password(clean_pw)

            if stored_hash != entered_hash:
                return False, None, "Invalid username or password."

            user = User(
                id=row["id"],
                name=row["name"],
                username=row["username"],
                password_hash=row["password_hash"],
                role=row["role"],
                email=row["email"] if "email" in row.keys() else None,
                semester=row["semester"] if "semester" in row.keys() else None,
                division=row["division"] if "division" in row.keys() else None,
                created_at=row["created_at"] if "created_at" in row.keys() else None
            )
            self._current_user = user
            return True, user, "Login successful."
        except sqlite3.Error as e:
            return False, None, f"Database error during login: {str(e)}"
        finally:
            conn.close()

    def logout(self) -> None:
        """Clear active user session."""
        self._current_user = None

    def change_password(self, user_id: int, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Change password for a given user after verifying old password."""
        if not new_password or len(new_password) < 4:
            return False, "New password must be at least 4 characters long."

        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT password_hash FROM users WHERE id = ?;", (user_id,))
            row = cursor.fetchone()
            if not row:
                return False, "User not found."

            if row["password_hash"] != hash_password(old_password):
                return False, "Current password does not match."

            new_hash = hash_password(new_password)
            cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?;", (new_hash, user_id))
            conn.commit()

            if self._current_user and self._current_user.id == user_id:
                self._current_user.password_hash = new_hash

            return True, "Password changed successfully."
        except sqlite3.Error as e:
            return False, f"Database error: {str(e)}"
        finally:
            conn.close()

    def update_profile(self, user_id: int, name: str, email: Optional[str], semester: Optional[str], division: Optional[str]) -> Tuple[bool, str]:
        """Update personal profile details."""
        if not name or not name.strip():
            return False, "Name cannot be empty."

        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE users 
                SET name = ?, email = ?, semester = ?, division = ?
                WHERE id = ?;
            """, (name.strip(), email.strip() if email else None, semester, division, user_id))
            conn.commit()

            if self._current_user and self._current_user.id == user_id:
                self._current_user.name = name.strip()
                self._current_user.email = email.strip() if email else None
                self._current_user.semester = semester
                self._current_user.division = division

            return True, "Profile updated successfully."
        except sqlite3.Error as e:
            return False, f"Database error: {str(e)}"
        finally:
            conn.close()
