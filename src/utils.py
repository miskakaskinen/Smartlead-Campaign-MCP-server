"""
Smartlead MCP Server - Utility Functions and API Client

This file contains utility functions and the API client for interacting with Smartlead.
"""

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx
from mcp.server.fastmcp import Context

logger = logging.getLogger(__name__)


class SmartleadAPIError(Exception):
    """Exception raised for Smartlead API errors."""

    def __init__(self, status_code: int, message: str, details: Optional[Dict[str, Any]] = None):
        self.status_code = status_code
        self.message = message
        self.details = details
        super().__init__(f"Smartlead API Error ({status_code}): {message}")


@dataclass
class SmartleadClient:
    """Client for interacting with the Smartlead API."""

    api_key: str
    api_url: str = "https://server.smartlead.ai/api/v1"
    timeout: int = 30
    http_client: Optional[httpx.AsyncClient] = None

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make a request to the Smartlead API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            params: Query parameters
            json_data: JSON data for POST/PUT requests
            headers: Additional HTTP headers
            
        Returns:
            API response as a dictionary
            
        Raises:
            SmartleadAPIError: If the API returns an error
        """
        url = f"{self.api_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Initialize params dict if None
        if params is None:
            params = {}
        
        # Add API key to query parameters
        params["api_key"] = self.api_key
        
        # Default headers
        default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Merge with custom headers if provided
        if headers:
            for key, value in headers.items():
                default_headers[key] = value

        try:
            if self.http_client:
                client = self.http_client
                close_client = False
            else:
                client = httpx.AsyncClient(timeout=self.timeout)
                close_client = True

            try:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    headers=default_headers,
                )

                try:
                    response_data = response.json()
                except json.JSONDecodeError:
                    response_data = {"message": response.text}

                if response.status_code >= 400:
                    error_message = response_data.get("message", "Unknown error")
                    error_details = response_data.get("errors", {})
                    raise SmartleadAPIError(
                        status_code=response.status_code,
                        message=error_message,
                        details=error_details,
                    )

                return response_data

            finally:
                if close_client:
                    await client.aclose()

        except httpx.RequestError as e:
            logger.error(f"Request error: {str(e)}")
            raise SmartleadAPIError(
                status_code=500,
                message=f"Request error: {str(e)}",
            )

    async def list_campaigns(self) -> Dict[str, Any]:
        """
        List all campaigns.

        Returns:
            List of campaigns:
            [
                {
                    "id": 372,
                    "user_id": 124,
                    "created_at": "2022-05-26T03:47:31.448094+00:00",
                    "updated_at": "2022-05-26T03:47:31.448094+00:00",
                    "status": "ACTIVE",  # ENUM (DRAFTED/ACTIVE/COMPLETED/STOPPED/PAUSED)
                    "name": "My Epic Campaign",
                    "track_settings": "DONT_REPLY_TO_AN_EMAIL",  # ENUM (DONT_EMAIL_OPEN/DONT_LINK_CLICK/DONT_REPLY_TO_AN_EMAIL)
                    "scheduler_cron_value": "{ tz: 'Australia/Sydney', days: [ 1, 2, 3, 4, 5 ], endHour: '23:00', startHour: '10:00' }",
                    "min_time_btwn_emails": 10,  # minutes
                    "max_leads_per_day": 10,
                    "parent_campaign_id": 13423,  # if null, it is a parent campaign, if not null then it's a subsequence
                    "stop_lead_settings": "REPLY_TO_AN_EMAIL",  # ENUM (REPLY_TO_AN_EMAIL/CLICK_ON_A_LINK/OPEN_AN_EMAIL)
                    "unsubscribe_text": "Don't Contact Me",
                    "client_id": 22  # null if not attached to a client
                },
                ...
            ]
        """
        return await self._request("GET", "campaigns/")

    async def get_campaign(self, campaign: str) -> Dict[str, Any]:
        """
        Get a campaign by ID.

        Args:
            campaign: The ID of the campaign you want to fetch

        Returns:
            Campaign details:
            {
                "id": 372,
                "user_id": 124,
                "created_at": "2022-05-26T03:47:31.448094+00:00",
                "updated_at": "2022-05-26T03:47:31.448094+00:00",
                "status": "ACTIVE",  # ENUM (DRAFTED/ACTIVE/COMPLETED/STOPPED/PAUSED)
                "name": "My Epic Campaign",
                "track_settings": "DONT_REPLY_TO_AN_EMAIL",  # ENUM (DONT_EMAIL_OPEN/DONT_LINK_CLICK/DONT_REPLY_TO_AN_EMAIL)
                "scheduler_cron_value": "{ tz: 'Australia/Sydney', days: [ 1, 2, 3, 4, 5 ], endHour: '23:00', startHour: '10:00' }",
                "min_time_btwn_emails": 10,  # minutes
                "max_leads_per_day": 10,
                "stop_lead_settings": "REPLY_TO_AN_EMAIL",  # ENUM (REPLY_TO_AN_EMAIL/CLICK_ON_A_LINK/OPEN_AN_EMAIL)
                "unsubscribe_text": "Don't Contact Me",
                "client_id": 23,  # null if the campaign is not attached to a client
                "enable_ai_esp_matching": true,  # leads will be matched with similar ESP mailboxes IF they exist
                "send_as_plain_text": true,  # emails for this campaign are sent as plain text
                "follow_up_percentage": 40  # the follow up percentage allocated - assumed 60% is new leads
            }
        """
        return await self._request("GET", f"campaigns/{campaign}")

    async def create_campaign(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a campaign.

        Args:
            campaign_data: Campaign creation data

        Returns:
            Created campaign details:
            {
                ok: true,
                id: 3023,
                name: "Test email campaign",
                created_at: "2022-11-07T16:23:24.025929+00:00"
            }
        """
        return await self._request("POST", "campaigns/create", json_data=campaign_data)

    async def update_campaign_schedule(
        self,
        campaign_id: str,
        timezone: str,
        days_of_the_week: List[int],
        start_hour: str,
        end_hour: str,
        min_time_btw_emails: Optional[int] = None,
        max_new_leads_per_day: Optional[int] = None,
        schedule_start_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update Campaign Schedule.

        Args:
            campaign_id: The ID of the campaign you want to update
            timezone: Timezone name in IANA format (e.g., "America/Los_Angeles", "Europe/Helsinki")
            days_of_the_week: A number value ranging from 0 to 6; i.e [0,1,2,3,4,5,6]
            start_hour: Time to start the campaign in 24-hour format (HH:MM), e.g., "01:11"
            end_hour: Time to end the campaign in 24-hour format (HH:MM), e.g., "02:22"
            min_time_btw_emails: Time in minutes between successive emails (defaults to 10)
            max_new_leads_per_day: Maximum number of new leads per day (defaults to 20)
            schedule_start_time: Standard ISO format accepted (defaults to current timestamp), e.g., "2023-04-25T07:29:25.978Z"

        Returns:
            Response:
            {
                "ok": true
            }
        """
        data = {
            "timezone": timezone,
            "days_of_the_week": days_of_the_week,
            "start_hour": start_hour,
            "end_hour": end_hour
        }
        if min_time_btw_emails is not None:
            data["min_time_btw_emails"] = min_time_btw_emails
        if max_new_leads_per_day is not None:
            data["max_new_leads_per_day"] = max_new_leads_per_day
        if schedule_start_time is not None:
            data["schedule_start_time"] = schedule_start_time

        return await self._request("POST", f"campaigns/{campaign_id}/schedule", json_data=data)

    async def update_campaign_settings(
        self,
        campaign_id: str,
        name: Optional[str] = None,
        track_settings: Optional[List[str]] = None,
        stop_lead_settings: Optional[str] = None,
        unsubscribe_text: Optional[str] = None,
        send_as_plain_text: Optional[bool] = None,
        force_plain_text: Optional[bool] = None,
        enable_ai_esp_matching: Optional[bool] = None,
        follow_up_percentage: Optional[int] = None,
        client_id: Optional[int] = None,
        add_unsubscribe_tag: Optional[bool] = None,
        auto_pause_domain_leads_on_reply: Optional[bool] = None,
        ignore_ss_mailbox_sending_limit: Optional[bool] = None,
        bounce_autopause_threshold: Optional[str] = None,
        out_of_office_detection_settings: Optional[Dict[str, Any]] = None,
        ai_categorisation_options: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Update Campaign General Settings to match the Smartlead API.

        Args:
            campaign_id: The ID of the campaign you want to update
            name: Name of the campaign (null means no name update)
            track_settings: List of tracking settings. Valid values: ["DONT_TRACK_EMAIL_OPEN", "DONT_TRACK_LINK_CLICK"]
            stop_lead_settings: Stops lead processing. Valid values: "REPLY_TO_AN_EMAIL", "CLICK_ON_A_LINK", "OPEN_AN_EMAIL"
            unsubscribe_text: Custom unsubscribe text (empty means no text)
            send_as_plain_text: Send emails as plain text (true/false)
            force_plain_text: Force emails to be plain text even if formatted (true/false)
            enable_ai_esp_matching: AI-enabled matching with email service providers (true/false)
            follow_up_percentage: Percent of leads to receive follow-ups (0-100)
            client_id: Client identifier (null if not specified)
            add_unsubscribe_tag: Add unsubscribe tag in emails (true/false)
            auto_pause_domain_leads_on_reply: Automatically pause domain leads on reply (true/false)
            ignore_ss_mailbox_sending_limit: Respect sending limit for shared mailboxes (true/false)
            bounce_autopause_threshold: Percentage of bounces to autopause campaign as a string (e.g., "5")
            out_of_office_detection_settings: Dictionary with the following keys:
                ignoreOOOasReply: Do not treat OOO responses as replies (true/false)
                autoReactivateOOO: Auto-reactivation for OOO responses (true/false)
                reactivateOOOwithDelay: Delay for reactivation in days (integer or null)
                autoCategorizeOOO: Automatically categorize OOO responses (true/false)
            ai_categorisation_options: List of category IDs for AI-based categorization (e.g., [2, 7, 1])

        Returns:
            Response:
            {
                "ok": true
            }
        """
        data = {}
        if name is not None:
            data["name"] = name
        if track_settings is not None:
            data["track_settings"] = track_settings
        if stop_lead_settings is not None:
            data["stop_lead_settings"] = stop_lead_settings
        if unsubscribe_text is not None:
            data["unsubscribe_text"] = unsubscribe_text
        if send_as_plain_text is not None:
            data["send_as_plain_text"] = send_as_plain_text
        if force_plain_text is not None:
            data["force_plain_text"] = force_plain_text
        if enable_ai_esp_matching is not None:
            data["enable_ai_esp_matching"] = enable_ai_esp_matching
        if follow_up_percentage is not None:
            data["follow_up_percentage"] = follow_up_percentage
        if client_id is not None:
            data["client_id"] = client_id
        if add_unsubscribe_tag is not None:
            data["add_unsubscribe_tag"] = add_unsubscribe_tag
        if auto_pause_domain_leads_on_reply is not None:
            data["auto_pause_domain_leads_on_reply"] = auto_pause_domain_leads_on_reply
        if ignore_ss_mailbox_sending_limit is not None:
            data["ignore_ss_mailbox_sending_limit"] = ignore_ss_mailbox_sending_limit
        if bounce_autopause_threshold is not None:
            data["bounce_autopause_threshold"] = bounce_autopause_threshold
        if out_of_office_detection_settings is not None:
            data["out_of_office_detection_settings"] = out_of_office_detection_settings
        if ai_categorisation_options is not None:
            data["ai_categorisation_options"] = ai_categorisation_options

        return await self._request("POST", f"campaigns/{campaign_id}/settings", json_data=data)

    async def save_campaign_sequence(
        self,
        campaign_id: str,
        sequences: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Save Campaign Sequence to match the Smartlead API.

        This endpoint saves a sequence within a campaign.

        IMPORTANT: Each sequence in the sequences array MUST include:
        - seq_number: The position in the sequence (1, 2, 3, etc.)
        - seq_delay_details: A dict with "delay_in_days" (required, cannot be 0 for follow-ups)
        
        For sequences with A/B testing, include these additional fields:
        - variant_distribution_type: "MANUAL_EQUAL", "MANUAL_PERCENTAGE", or "AI_EQUAL"
        - winning_metric_property: For AI_EQUAL - "OPEN_RATE", "CLICK_RATE", "REPLY_RATE", or "POSITIVE_REPLY_RATE"
        - lead_distribution_percentage: For AI_EQUAL - percent of leads for testing (minimum 20%)
        - seq_variants: Array of variant objects with required fields:
          - subject: Email subject line
          - email_body: HTML content of the email
          - variant_label: Label for the variant (e.g., "A", "B", "C")
          - variant_distribution_percentage: For MANUAL_PERCENTAGE - percentage allocation
        
        For simple follow-up sequences, include:
        - subject: If blank, makes the follow-up in the same thread
        - email_body: HTML content of the email
        
        Example payload formats:
        
        1. For equal distribution between variants:
        ```
        {
          "seq_number": 1,
          "seq_delay_details": {"delay_in_days": 1},
          "variant_distribution_type": "MANUAL_EQUAL",
          "seq_variants": [
            {
              "subject": "Subject A",
              "email_body": "<p>Email content for A</p>",
              "variant_label": "A"
            },
            {
              "subject": "Subject B",
              "email_body": "<p>Email content for B</p>",
              "variant_label": "B"
            }
          ]
        }
        ```
        
        2. For percentage-based distribution:
        ```
        {
          "seq_number": 1,
          "seq_delay_details": {"delay_in_days": 1},
          "variant_distribution_type": "MANUAL_PERCENTAGE",
          "seq_variants": [
            {
              "subject": "Subject A",
              "email_body": "<p>Content A</p>",
              "variant_label": "A",
              "variant_distribution_percentage": 20
            },
            {
              "subject": "Subject B",
              "email_body": "<p>Content B</p>",
              "variant_label": "B",
              "variant_distribution_percentage": 60
            },
            {
              "subject": "Subject C",
              "email_body": "<p>Content C</p>",
              "variant_label": "C",
              "variant_distribution_percentage": 20
            }
          ]
        }
        ```
        
        3. For AI-based optimization:
        ```
        {
          "seq_number": 1,
          "seq_delay_details": {"delay_in_days": 1},
          "variant_distribution_type": "AI_EQUAL",
          "winning_metric_property": "OPEN_RATE",
          "lead_distribution_percentage": 40,
          "seq_variants": [
            {
              "subject": "Subject A",
              "email_body": "<p>Content A</p>",
              "variant_label": "A"
            },
            {
              "subject": "Subject B",
              "email_body": "<p>Content B</p>",
              "variant_label": "B"
            }
          ]
        }
        ```
        
        4. For simple follow-up (no variants):
        ```
        {
          "seq_number": 2,
          "seq_delay_details": {"delay_in_days": 1},
          "subject": "",
          "email_body": "<p>Bump up right!</p>"
        }
        ```

        Args:
            campaign_id: The ID of the campaign to save sequence for
            sequences: The email sequence array with all required fields

        Returns:
            Response:
            {
                "ok": true,
                "data": "success"
            }
        """
        data = {
            "sequences": sequences
        }
        return await self._request("POST", f"campaigns/{campaign_id}/sequences", json_data=data)

    async def patch_campaign_status(
        self,
        campaign_id: str,
        status: str
    ) -> Dict[str, Any]:
        """
        Patch campaign status.

        This endpoint changes the status of a campaign.

        Args:
            campaign_id: The ID of the campaign you want to patch
            status: Patch status. Must be exactly one of: "PAUSED", "STOPPED", or "START"

        Returns:
            Response:
            {
                "ok": true
            }
        """
        data = {
            "status": status
        }
        return await self._request("POST", f"campaigns/{campaign_id}/status", json_data=data)

    async def get_campaign_analytics(
        self,
        campaignId: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Fetch Campaign Analytics by Date range

        This endpoint fetches campaign-specific analytics for a specified date range

        Args:
            campaignId: The ID of the campaign
            start_date: Starting point for the date range (YYYY-MM-DD)
            end_date: Ending point for the date range (YYYY-MM-DD)

        Returns:
            Response:
            {
                "id": 1562695,
                "user_id": [user_id],
                "created_at": "2025-02-24T11:51:47.872Z",
                "status": "COMPLETED",
                "name": "Test campaign to check  - copy",
                "start_date": "2025-01-29",
                "end_date": "2025-02-25",
                "sent_count": "30",
                "unique_sent_count": "10",
                "open_count": "5",
                "unique_open_count": "2",
                "click_count": "0",
                "unique_click_count": "0",
                "reply_count": "0",
                "block_count": "0",
                "total_count": "30",
                "drafted_count": "0",
                "bounce_count": "0",
                "unsubscribed_count": "0"
            }
        """
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        return await self._request("GET", f"campaigns/{campaignId}/analytics-by-date", params=params)

    async def get_campaign_sequence(
        self,
        campaign_id: str
    ) -> Dict[str, Any]:
        """
        Fetch Campaign Sequence By Campaign ID

        This endpoint fetches a campaign's sequence data

        Args:
            campaign_id: The ID of the campaign you want to fetch sequence for

        Returns:
            Response:
            {
                "id": 8494,
                "created_at": "2022-11-08T07:06:35.990Z",
                "updated_at": "2022-11-08T07:34:03.667Z",
                "email_campaign_id": 3070,
                "seq_number": 1,
                "subject": "",
                "email_body": "",
                "sequence_variants": [
                    {
                        "id": 2535,
                        "created_at": "2022-11-08T07:06:36.002558+00:00",
                        "updated_at": "2022-11-08T07:34:04.026626+00:00",
                        "is_deleted": false,
                        "subject": "Subject",
                        "email_body": "<p>Hi<br><br>How are you?<br><br>Hope you're doing good</p>",
                        "email_campaign_seq_id": 8494,
                        "variant_label": "A"
                    },
                    {
                        "id": 2536,
                        "created_at": "2022-11-08T07:06:36.002558+00:00",
                        "updated_at": "2022-11-08T07:34:04.373866+00:00",
                        "is_deleted": false,
                        "subject": "Ema a",
                        "email_body": "<p>This is a new game a</p>",
                        "email_campaign_seq_id": 8494,
                        "variant_label": "B"
                    },
                    {
                        "id": 2537,
                        "created_at": "2022-11-08T07:06:36.002558+00:00",
                        "updated_at": "2022-11-08T07:34:04.721608+00:00",
                        "is_deleted": false,
                        "subject": "C emsil",
                        "email_body": "<p>Hiii C</p>",
                        "email_campaign_seq_id": 8494,
                        "variant_label": "C"
                    }
                ]
            }
        """
        return await self._request("GET", f"campaigns/{campaign_id}/sequences")

    async def get_campaigns_by_lead_id(
        self,
        lead_id: str
    ) -> Dict[str, Any]:
        """
        Fetch all Campaigns Using Lead ID

        This endpoint lets you fetch all the campaigns a Lead belongs to using the Lead ID

        Args:
            lead_id: The target lead ID

        Returns:
            Response:
            [
                {
                    "id": 2011,
                    "status": "COMPLETED",
                    "name": "SL - High Intent Leads guide"
                },
                {
                    "id": 5055,
                    "status": "DRAFTED",
                    "name": ""
                }
            ]
        """
        return await self._request("GET", f"leads/{lead_id}/campaigns")

    async def export_campaign_data(
        self,
        campaign_id: str
    ) -> Dict[str, Any]:
        """
        Export data from a campaign

        This endpoint returns a CSV file of all leads from a campaign using the campaign's ID

        Args:
            campaign_id: The ID of the campaign you want to fetch data from

        Returns:
            CSV formatted data with the following columns:
            id - integer
            campaign_lead_map_id - integer
            status - text
            created_at - timestamp with time zone
            first_name - text
            last_name - text
            email - text
            phone_number - text
            company_name - text
            website - text
            location - text
            custom_fields - jsonb
            linkedin_profile - text
            company_url - text
            is_unsubscribed - boolean
            last_email_sequence_sent - integer
            is_interested - boolean
            open_count - integer
            click_count - integer
            reply_count - integer
        """
        headers = {"Accept": "text/plain"}
        return await self._request("GET", f"campaigns/{campaign_id}/leads-export", headers=headers)

    async def get_campaign_sequence_analytics(
        self,
        campaign_id: str,
        start_date: str,
        end_date: str,
        time_zone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get Campaign Sequence Analytics

        Retrieves analytics data for a specific email campaign sequence, including sent count,
        open count, click count, and other engagement metrics.

        Args:
            campaign_id: The ID of the campaign to fetch analytics for
            start_date: Start date in YYYY-MM-DD HH:MM:SS format
            end_date: End date in YYYY-MM-DD HH:MM:SS format
            time_zone: Timezone for the date ranges (e.g., 'Europe/London')

        Returns:
            Response:
            {
                "ok": true,
                "data": [
                    {
                        "email_campaign_seq_id": 2868271,
                        "sent_count": 6,
                        "skipped_count": 0,
                        "open_count": 2,
                        "click_count": 0,
                        "reply_count": 0,
                        "bounce_count": 0,
                        "unsubscribed_count": 0,
                        "failed_count": 0,
                        "stopped_count": 0,
                        "ln_connection_req_pending_count": 0,
                        "ln_connection_req_accepted_count": 0,
                        "ln_connection_req_skipped_sent_msg_count": 0,
                        "positive_reply_count": 0
                    }
                ]
            }
        """
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        if time_zone:
            params["time_zone"] = time_zone
            
        return await self._request("GET", f"campaigns/{campaign_id}/sequence-analytics", params=params)


def validate_environment() -> None:
    """
    Validate required environment variables are set.
    
    Raises:
        ValueError: If any required environment variables are missing
    """
    required_vars = ["SMARTLEAD_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")


def format_response(data: Any) -> str:
    """
    Format API response data as a readable string for MCP protocol.
    
    Args:
        data: The data to format
        
    Returns:
        str: A formatted string representation of the data suitable for MCP
    """
    try:
        if isinstance(data, (dict, list)):
            # Ensure the response is a clean, single-line string for the agent
            return json.dumps(data, ensure_ascii=False)
        return str(data)
    except Exception as e:
        logger.error(f"Error formatting response: {str(e)}")
        return f"Error formatting response: {str(e)}"


async def get_client_from_context(ctx: Context) -> 'SmartleadClient':
    """
    Helper function to get the Smartlead client from the context with validation.
    
    Args:
        ctx: The Context provided by the MCP server
        
    Returns:
        SmartleadClient: The initialized Smartlead API client
        
    Raises:
        ValueError: If the client is not properly initialized
    """
    if not hasattr(ctx.request_context, "lifespan_context"):
        raise ValueError("Request context not properly initialized")
        
    if not hasattr(ctx.request_context.lifespan_context, "smartlead_client"):
        raise ValueError("Smartlead client not found in context")
    
    client = ctx.request_context.lifespan_context.smartlead_client
    if not isinstance(client, SmartleadClient):
        raise ValueError("Invalid Smartlead client type in context")
    
    return client


def handle_api_error(e: Exception) -> str:
    """
    Handle API errors and return a formatted error message.
    
    Args:
        e: The exception to handle
        
    Returns:
        str: A formatted error message
    """
    if isinstance(e, SmartleadAPIError):
        error_msg = f"Error ({e.status_code}): {e.message}"
        if e.details:
            error_msg += f"\nDetails: {json.dumps(e.details, indent=2)}"
        return error_msg
    
    return f"Error: {str(e)}" 