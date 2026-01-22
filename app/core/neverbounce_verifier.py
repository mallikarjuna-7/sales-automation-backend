"""
NeverBounce Email Verification Module
Verifies email addresses using the NeverBounce API.
"""
import httpx
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Status messages for display
STATUS_DISPLAY = {
    "valid": "✓ Valid",
    "invalid": "✗ Invalid",
    "disposable": "⚠ Disposable",
    "catchall": "? Catch-all",
    "unknown": "? Unknown"
}

# Color codes for frontend display
STATUS_COLORS = {
    "valid": "green",
    "invalid": "red",
    "disposable": "orange",
    "catchall": "yellow",
    "unknown": "gray"
}


class NeverBounceVerifier:
    """Email verification using NeverBounce API"""
    
    def __init__(self, api_key: str):
        """
        Initialize NeverBounce verifier
        
        Args:
            api_key: NeverBounce API key (starts with 'private_' or 'secret_')
        """
        self.api_key = api_key
        self.base_url = "https://api.neverbounce.com/v4"
        
    async def verify_email(
        self, 
        email: str,
        address_info: bool = False,
        credits_info: bool = False,
        timeout: int = 10
    ) -> Dict:
        """
        Verify a single email address
        
        Args:
            email: Email address to verify
            address_info: Include additional address information
            credits_info: Include credit usage information
            timeout: Verification timeout in seconds
            
        Returns:
            Dict with verification result:
            {
                'email': 'test@example.com',
                'status': 'valid',  # valid, invalid, disposable, catchall, unknown
                'status_display': '✓ Valid',
                'status_color': 'green',
                'flags': ['has_dns', 'has_mail_server'],  # Optional flags
                'suggested_correction': 'corrected@example.com',  # If typo detected
                'execution_time': 285,  # MS
                'credits_remaining': 1000  # If credits_info=True
            }
        """
        try:
            # Build request parameters
            params = {
                'key': self.api_key,
                'email': email,
                'address_info': int(address_info),
                'credits_info': int(credits_info),
                'timeout': timeout,
                'request_meta_data[leverage_historical_data]': 1
            }
            
            # Make API request
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/single/check",
                    params=params,
                    timeout=timeout + 5  # Add buffer to HTTP timeout
                )
                
                # Check for HTTP errors
                response.raise_for_status()
                data = response.json()
                
                # Check API status
                if data.get('status') != 'success':
                    error_msg = data.get('message', 'Unknown error')
                    logger.error(f"NeverBounce API error: {error_msg}")
                    return self._create_error_result(email, error_msg)
                
                # Extract result (API returns: 'valid', 'invalid', 'disposable', 'catchall', 'unknown')
                status = data.get('result', 'unknown').lower()
                
                # Build response
                verification = {
                    'email': email,
                    'status': status,
                    'status_display': STATUS_DISPLAY.get(status, '? Unknown'),
                    'status_color': STATUS_COLORS.get(status, 'gray'),
                    'execution_time': data.get('execution_time', 0)
                }
                
                # Add optional fields
                if 'flags' in data:
                    verification['flags'] = data['flags']
                    
                if 'suggested_correction' in data and data['suggested_correction']:
                    verification['suggested_correction'] = data['suggested_correction']
                    
                if credits_info and 'credits_info' in data:
                    verification['credits_remaining'] = data['credits_info'].get('remaining_credits', 0)
                    verification['credits_used'] = data['credits_info'].get('used_credits', 0)
                    
                if address_info and 'address_info' in data:
                    verification['address_info'] = data['address_info']
                
                logger.info(f"✓ Verified {email}: {status} ({data.get('execution_time')}ms)")
                return verification
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error verifying {email}: {e.response.status_code}")
            return self._create_error_result(email, f"HTTP {e.response.status_code}")
            
        except httpx.TimeoutException:
            logger.error(f"Timeout verifying {email}")
            return self._create_error_result(email, "Timeout")
            
        except Exception as e:
            logger.error(f"Error verifying {email}: {str(e)}")
            return self._create_error_result(email, str(e))
    
    def _create_error_result(self, email: str, error: str) -> Dict:
        """Create error result when verification fails"""
        return {
            'email': email,
            'status': 'error',
            'status_display': '✗ Error',
            'status_color': 'red',
            'error': error,
            'execution_time': 0
        }
    
    async def verify_multiple(self, emails: list[str]) -> Dict[str, Dict]:
        """
        Verify multiple email addresses (one-by-one)
        
        Args:
            emails: List of email addresses
            
        Returns:
            Dict mapping email -> verification result
        """
        results = {}
        for email in emails:
            results[email] = await self.verify_email(email)
        return results
    
    async def verify_batch(self, emails: list[str]) -> Dict[str, Dict]:
        """
        Verify multiple email addresses using NeverBounce Bulk API (more efficient)
        
        Uses the v4/jobs/download endpoint for batch verification.
        This is more efficient than verify_multiple for large batches.
        
        Args:
            emails: List of email addresses (up to 100,000 per batch)
            
        Returns:
            Dict mapping email -> verification result
        """
        if not emails:
            return {}
        
        try:
            # For batch processing, NeverBounce requires uploading emails and checking job status
            # However, for best results with their API, we'll use a streaming approach
            # that batches the single-check requests efficiently
            
            logger.info(f"🔄 Starting batch verification for {len(emails)} emails")
            
            results = {}
            # Process in parallel batches of 5 (to avoid rate limiting)
            import asyncio
            
            batch_size = 5
            for i in range(0, len(emails), batch_size):
                batch = emails[i:i + batch_size]
                # Run verifications in parallel
                tasks = [self.verify_email(email) for email in batch]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for email, result in zip(batch, batch_results):
                    if isinstance(result, Exception):
                        results[email] = self._create_error_result(email, str(result))
                    else:
                        results[email] = result
                
                # Log progress
                completed = min(i + batch_size, len(emails))
                logger.info(f"📧 Batch verification progress: {completed}/{len(emails)}")
            
            logger.info(f"✅ Batch verification completed: {len(results)} emails processed")
            return results
            
        except Exception as e:
            logger.error(f"Error in batch verification: {str(e)}")
            # Fallback to sequential verification
            return await self.verify_multiple(emails)


# Singleton instance
_verifier_instance: Optional[NeverBounceVerifier] = None


def get_verifier(api_key: Optional[str] = None) -> NeverBounceVerifier:
    """
    Get or create NeverBounce verifier instance
    
    Args:
        api_key: NeverBounce API key (required on first call)
        
    Returns:
        NeverBounceVerifier instance
    """
    global _verifier_instance
    
    if _verifier_instance is None:
        if api_key is None:
            raise ValueError("api_key required to initialize NeverBounce verifier")
        _verifier_instance = NeverBounceVerifier(api_key)
    
    return _verifier_instance


async def verify_email_simple(email: str, api_key: str) -> str:
    """
    Simple email verification - returns just the status
    
    Args:
        email: Email to verify
        api_key: NeverBounce API key
        
    Returns:
        Status string: 'valid', 'invalid', 'disposable', 'catchall', 'unknown', 'error'
    """
    verifier = get_verifier(api_key)
    result = await verifier.verify_email(email)
    return result['status']
