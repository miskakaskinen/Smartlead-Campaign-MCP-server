"""
Smartlead MCP Server - Main Entry Point

This file implements a FastMCP server that exposes Smartlead API endpoints as tools.

Required Environment Variables:
- SMARTLEAD_API_KEY: Your Smartlead API key
- SMARTLEAD_API_URL: Smartlead API URL (defaults to https://server.smartlead.ai/api/v1)
- TRANSPORT: Transport protocol (sse or stdio)
- HOST: Host to bind to when using SSE transport (defaults to 0.0.0.0)
- PORT: Port to listen on when using SSE transport (defaults to 8050)
"""

import asyncio
import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# Add debug print statements to help diagnose issues
print("Starting Smartlead MCP server...", file=sys.stderr)
print(f"Python version: {sys.version}", file=sys.stderr)
print(f"Environment: {os.environ.get('TRANSPORT', 'not set')}", file=sys.stderr)
print(f"Current directory: {os.getcwd()}", file=sys.stderr)
print("Environment variables received:", file=sys.stderr)
print(f"SMARTLEAD_API_KEY: {'set' if os.environ.get('SMARTLEAD_API_KEY') else 'not set'}", file=sys.stderr)
print(f"SMARTLEAD_API_URL: {os.environ.get('SMARTLEAD_API_URL', 'not set')}", file=sys.stderr)
print(f"LOG_LEVEL: {os.environ.get('LOG_LEVEL', 'not set')}", file=sys.stderr)

from mcp.server.fastmcp import Context, FastMCP
import httpx

from src.utils import (
    SmartleadClient,
    handle_api_error,
    format_response,
    get_client_from_context,
    validate_environment,
)

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class SmartleadContext:
    """Context for the Smartlead MCP server."""
    smartlead_client: SmartleadClient


@asynccontextmanager
async def smartlead_lifespan(server: FastMCP) -> AsyncIterator[SmartleadContext]:
    """
    Manages the Smartlead API client lifecycle.
    
    Args:
        server: The FastMCP server instance
        
    Yields:
        SmartleadContext: The context containing the Smartlead API client
    """
    # Validate environment variables
    validate_environment()
    
    # Get API key and URL from environment variables
    api_key = os.getenv("SMARTLEAD_API_KEY")
    api_url = os.getenv("SMARTLEAD_API_URL", "https://server.smartlead.ai/api/v1")
    
    # Create the Smartlead API client
    smartlead_client = SmartleadClient(api_key=api_key, api_url=api_url)
    
    try:
        logger.info("Smartlead API client initialized")
        yield SmartleadContext(smartlead_client=smartlead_client)
    finally:
        logger.info("Shutting down Smartlead API client")
        await smartlead_client.close()


# Initialize FastMCP server
mcp = FastMCP(
    "smartlead-mcp",
    description="MCP server for interacting with the Smartlead API",
    lifespan=smartlead_lifespan,
    host=os.getenv("HOST", "0.0.0.0"),
    port=int(os.getenv("PORT", "8050"))
)


@mcp.tool()
async def list_campaigns(ctx: Context) -> str:
    """List all Campaigns
    
    This endpoint fetches all the campaigns in your account
    
    Args:
        ctx: The context provided by the MCP server
    
    Returns:
        A JSON formatted response:
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
    try:
        client = await get_client_from_context(ctx)
        response = await client.list_campaigns()
        return format_response(response)
    except Exception as e:
        logger.error(f"Error listing campaigns: {str(e)}")
        return handle_api_error(e)


@mcp.tool()
async def get_campaign(ctx: Context, campaign: str) -> str:
    """Get Campaign By Id
    
    This endpoint fetches a campaign based on its ID
    
    Args:
        ctx: The context provided by the MCP server
        campaign: The ID of the campaign you want to fetch
    
    Returns:
        A JSON formatted response:
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
    try:
        client = await get_client_from_context(ctx)
        response = await client.get_campaign(campaign)
        return format_response(response)
    except Exception as e:
        logger.error(f"Error getting campaign {campaign}: {str(e)}")
        return handle_api_error(e)


@mcp.tool()
async def create_campaign(ctx: Context, campaign_data: Dict[str, Any]) -> str:
    """Create Campaign
    
    This endpoint creates a campaign
    
    Args:
        ctx: The context provided by the MCP server
        campaign_data: Campaign creation data
    
    Returns:
        A JSON formatted response:
        {
            ok: true,
            id: 3023,
            name: "Test email campaign",
            created_at: "2022-11-07T16:23:24.025929+00:00"
        }
    """
    try:
        client = await get_client_from_context(ctx)
        response = await client.create_campaign(campaign_data)
        return format_response(response)
    except Exception as e:
        logger.error(f"Error creating campaign: {str(e)}")
        return handle_api_error(e)


@mcp.tool()
async def update_campaign_schedule(
    ctx: Context,
    campaign_id: str,
    timezone: str,
    days_of_the_week: List[int],
    start_hour: str,
    end_hour: str,
    min_time_btw_emails: Optional[int] = None,
    max_new_leads_per_day: Optional[int] = None,
    schedule_start_time: Optional[str] = None
) -> str:
    """Update Campaign Schedule
    
    This endpoint updates a campaign's schedule
    
    Args:
        ctx: The context provided by the MCP server
        campaign_id: The ID of the campaign you want to update
        timezone: Timezone name in IANA format (e.g., "America/Los_Angeles", "Europe/Helsinki")
        days_of_the_week: A number value ranging from 0 to 6; i.e [0,1,2,3,4,5,6]
        start_hour: Time to start the campaign in 24-hour format (HH:MM), e.g., "01:11"
        end_hour: Time to end the campaign in 24-hour format (HH:MM), e.g., "02:22"
        min_time_btw_emails: Time in minutes between successive emails (defaults to 10)
        max_new_leads_per_day: Maximum number of new leads per day (defaults to 20)
        schedule_start_time: Standard ISO format accepted (defaults to current timestamp), e.g., "2023-04-25T07:29:25.978Z"
    
    Returns:
        A JSON formatted response:
        {
            "ok": true
        }
    """
    try:
        client = await get_client_from_context(ctx)
        response = await client.update_campaign_schedule(
            campaign_id=campaign_id,
            timezone=timezone,
            days_of_the_week=days_of_the_week,
            start_hour=start_hour,
            end_hour=end_hour,
            min_time_btw_emails=min_time_btw_emails,
            max_new_leads_per_day=max_new_leads_per_day,
            schedule_start_time=schedule_start_time
        )
        return format_response(response)
    except Exception as e:
        logger.error(f"Error updating campaign schedule for {campaign_id}: {str(e)}")
        return handle_api_error(e)


@mcp.tool()
async def update_campaign_settings(
    ctx: Context,
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
) -> str:
    """Update Campaign General Settings
    
    This endpoint updates a campaign's general settings.
    
    Args:
        ctx: The context provided by the MCP server
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
        A JSON formatted response:
        {
            "ok": true
        }
    """
    try:
        client = await get_client_from_context(ctx)
        response = await client.update_campaign_settings(
            campaign_id=campaign_id,
            name=name,
            track_settings=track_settings,
            stop_lead_settings=stop_lead_settings,
            unsubscribe_text=unsubscribe_text,
            send_as_plain_text=send_as_plain_text,
            force_plain_text=force_plain_text,
            enable_ai_esp_matching=enable_ai_esp_matching,
            follow_up_percentage=follow_up_percentage,
            client_id=client_id,
            add_unsubscribe_tag=add_unsubscribe_tag,
            auto_pause_domain_leads_on_reply=auto_pause_domain_leads_on_reply,
            ignore_ss_mailbox_sending_limit=ignore_ss_mailbox_sending_limit,
            bounce_autopause_threshold=bounce_autopause_threshold,
            out_of_office_detection_settings=out_of_office_detection_settings,
            ai_categorisation_options=ai_categorisation_options
        )
        return format_response(response)
    except Exception as e:
        logger.error(f"Error updating campaign settings for {campaign_id}: {str(e)}")
        return handle_api_error(e)


@mcp.tool()
async def save_campaign_sequence(
    ctx: Context,
    campaign_id: str,
    sequences: List[Dict[str, Any]]
) -> str:
    """Save Campaign Sequence
    
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
    
    Example payload:
    ```
    {
      "sequences": [
        {
          "seq_number": 1,
          "seq_delay_details": {
            "delay_in_days": 1
          },
          "variant_distribution_type": "MANUAL_EQUAL",
          "seq_variants": [
            {
              "subject": "Subject",
              "email_body": "<p>Hi<br><br>How are you?<br><br>Hope you're doing good</p>",
              "variant_label": "A"
            },
            {
              "subject": "Ema a",
              "email_body": "<p>This is a new game a</p>",
              "variant_label": "B"
            }
          ]
        },
        {
          "seq_number": 2,
          "seq_delay_details": {
            "delay_in_days": 1
          },
          "subject": "",
          "email_body": "<p>Bump up right!</p>"
        }
      ]
    }
    ```
    
    For MANUAL_PERCENTAGE distribution, include variant_distribution_percentage in each variant:
    ```
    {
      "seq_number": 1,
      "seq_delay_details": { "delay_in_days": 1 },
      "variant_distribution_type": "MANUAL_PERCENTAGE",
      "seq_variants": [
        {
          "subject": "Subject A",
          "email_body": "<p>Variant A content</p>",
          "variant_label": "A",
          "variant_distribution_percentage": 20
        },
        {
          "subject": "Subject B",
          "email_body": "<p>Variant B content</p>",
          "variant_label": "B",
          "variant_distribution_percentage": 60
        },
        {
          "subject": "Subject C",
          "email_body": "<p>Variant C content</p>",
          "variant_label": "C",
          "variant_distribution_percentage": 20
        }
      ]
    }
    ```
    
    For AI_EQUAL distribution, include winning_metric_property and lead_distribution_percentage:
    ```
    {
      "seq_number": 1,
      "seq_delay_details": { "delay_in_days": 1 },
      "variant_distribution_type": "AI_EQUAL",
      "winning_metric_property": "OPEN_RATE",
      "lead_distribution_percentage": 40,
      "seq_variants": [...]
    }
    ```
    
    Args:
        ctx: The context provided by the MCP server
        campaign_id: The ID of the campaign to save sequence for
        sequences: The email sequence array with all required fields
    
    Returns:
        A JSON formatted response:
        {
            "ok": true,
            "data": "success"
        }
    """
    try:
        client = await get_client_from_context(ctx)
        response = await client.save_campaign_sequence(
            campaign_id=campaign_id,
            sequences=sequences
        )
        return format_response(response)
    except Exception as e:
        logger.error(f"Error saving sequence for campaign {campaign_id}: {str(e)}")
        return handle_api_error(e)


@mcp.tool()
async def patch_campaign_status(
    ctx: Context,
    campaign_id: str,
    status: str
) -> str:
    """Patch campaign status
    
    This endpoint changes the status of a campaign.
    
    Args:
        ctx: The context provided by the MCP server
        campaign_id: The ID of the campaign you want to patch
        status: Patch status. Must be exactly one of: "PAUSED", "STOPPED", or "START"
    
    Returns:
        A JSON formatted response:
        {
            "ok": true
        }
    """
    try:
        client = await get_client_from_context(ctx)
        response = await client.patch_campaign_status(
            campaign_id=campaign_id,
            status=status
        )
        return format_response(response)
    except Exception as e:
        logger.error(f"Error updating campaign status for {campaign_id}: {str(e)}")
        return handle_api_error(e)


@mcp.tool()
async def get_campaign_analytics(
    ctx: Context,
    campaignId: str,
    start_date: str,
    end_date: str
) -> str:
    """Fetch Campaign Analytics by Date range
    
    This endpoint fetches campaign-specific analytics for a specified date range
    
    Args:
        ctx: The context provided by the MCP server
        campaignId: The ID of the campaign
        start_date: Starting point for the date range (YYYY-MM-DD)
        end_date: Ending point for the date range (YYYY-MM-DD)
    
    Returns:
        A JSON formatted response:
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
    try:
        client = await get_client_from_context(ctx)
        response = await client.get_campaign_analytics(
            campaignId=campaignId,
            start_date=start_date,
            end_date=end_date
        )
        return format_response(response)
    except Exception as e:
        logger.error(f"Error getting analytics for campaign {campaignId}: {str(e)}")
        return handle_api_error(e)


@mcp.tool()
async def get_campaign_sequence(
    ctx: Context,
    campaign_id: str
) -> str:
    """Fetch Campaign Sequence By Campaign ID
    
    This endpoint fetches a campaign's sequence data
    
    Args:
        ctx: The context provided by the MCP server
        campaign_id: The ID of the campaign you want to fetch sequence for
    
    Returns:
        A JSON formatted response:
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
    try:
        client = await get_client_from_context(ctx)
        response = await client.get_campaign_sequence(campaign_id)
        return format_response(response)
    except Exception as e:
        logger.error(f"Error getting sequence for campaign {campaign_id}: {str(e)}")
        return handle_api_error(e)


@mcp.tool()
async def get_campaigns_by_lead_id(
    ctx: Context,
    lead_id: str
) -> str:
    """Fetch all Campaigns Using Lead ID
    
    This endpoint lets you fetch all the campaigns a Lead belongs to using the Lead ID
    
    Args:
        ctx: The context provided by the MCP server
        lead_id: The target lead ID
    
    Returns:
        A JSON formatted list of campaigns that the lead belongs to:
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
    try:
        client = await get_client_from_context(ctx)
        response = await client.get_campaigns_by_lead_id(lead_id)
        return format_response(response)
    except Exception as e:
        logger.error(f"Error getting campaigns for lead {lead_id}: {str(e)}")
        return handle_api_error(e)


@mcp.tool()
async def export_campaign_data(
    ctx: Context,
    campaign_id: str
) -> str:
    """Export data from a campaign
    
    This endpoint returns a CSV file of all leads from a campaign using the campaign's ID
    
    Args:
        ctx: The context provided by the MCP server
        campaign_id: The ID of the campaign you want to fetch data from
    
    Returns:
        A CSV formatted response with the following columns:
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
    try:
        client = await get_client_from_context(ctx)
        response = await client.export_campaign_data(campaign_id)
        return format_response(response)
    except Exception as e:
        logger.error(f"Error exporting data for campaign {campaign_id}: {str(e)}")
        return handle_api_error(e)


@mcp.tool()
async def get_campaign_sequence_analytics(
    ctx: Context,
    campaign_id: str,
    start_date: str,
    end_date: str,
    time_zone: Optional[str] = None
) -> str:
    """Get Campaign Sequence Analytics
    
    Retrieves analytics data for a specific email campaign sequence, including sent count,
    open count, click count, and other engagement metrics.
    
    Args:
        ctx: The context provided by the MCP server
        campaign_id: The ID of the campaign to fetch analytics for
        start_date: Start date in YYYY-MM-DD HH:MM:SS format
        end_date: End date in YYYY-MM-DD HH:MM:SS format
        time_zone: Timezone for the date ranges (e.g., 'Europe/London')
    
    Returns:
        A JSON formatted response:
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
    try:
        client = await get_client_from_context(ctx)
        response = await client.get_campaign_sequence_analytics(
            campaign_id=campaign_id,
            start_date=start_date,
            end_date=end_date,
            time_zone=time_zone
        )
        return format_response(response)
    except Exception as e:
        logger.error(f"Error getting sequence analytics for campaign {campaign_id}: {str(e)}")
        return handle_api_error(e)


async def main():
    transport = os.getenv("TRANSPORT", "sse")
    if transport == 'sse':
        # Run the MCP server with sse transport
        await mcp.run_sse_async()
    else:
        # Run the MCP server with stdio transport
        await mcp.run_stdio_async()


if __name__ == "__main__":
    asyncio.run(main()) 