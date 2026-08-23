from typing import Optional
from supabase import create_client, Client, ClientOptions
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("app.services.supabase")

class SupabaseClientManager:
    """
    Manages Supabase Client lifecycle, authentication headers, and RLS scoping.
    """

    def __init__(self):
        self._anon_client: Optional[Client] = None
        self._service_client: Optional[Client] = None

    def get_anon_client(self) -> Optional[Client]:
        """
        Returns standard publishable Supabase client (using anon key).
        """
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            logger.debug("Supabase URL or Key not configured; running in detached mode")
            return None

        if self._anon_client is None:
            try:
                self._anon_client = create_client(
                    supabase_url=settings.SUPABASE_URL,
                    supabase_key=settings.SUPABASE_KEY
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Supabase anon client: {e}")
                return None

        return self._anon_client

    def get_user_scoped_client(self, user_jwt: Optional[str]) -> Optional[Client]:
        """
        Returns a Supabase client configured with the user's JWT Bearer token.
        Ensures all PostgreSQL queries execute strictly under the user's auth context,
        enforcing database Row Level Security (RLS) policies.
        """
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            return None

        if not user_jwt:
            return self.get_anon_client()

        try:
            # Create client with custom authorization header containing user's JWT
            options = ClientOptions(
                headers={"Authorization": f"Bearer {user_jwt}"}
            )
            return create_client(
                supabase_url=settings.SUPABASE_URL,
                supabase_key=settings.SUPABASE_KEY,
                options=options
            )
        except Exception as e:
            logger.warning(f"Failed to create user-scoped Supabase client: {e}")
            return self.get_anon_client()

    def get_service_role_client(self) -> Optional[Client]:
        """
        Returns admin service role client (only if SUPABASE_SERVICE_ROLE_KEY is configured).
        """
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
            return None

        if self._service_client is None:
            try:
                self._service_client = create_client(
                    supabase_url=settings.SUPABASE_URL,
                    supabase_key=settings.SUPABASE_SERVICE_ROLE_KEY
                )
            except Exception as e:
                logger.error(f"Failed to initialize Supabase service role client: {e}")
                return None

        return self._service_client

supabase_manager = SupabaseClientManager()
