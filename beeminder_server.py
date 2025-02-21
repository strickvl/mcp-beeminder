import os
from logging import getLogger
from typing import Optional

from beeminder_client.beeminder import BeeminderAPI
from beeminder_client.models import BeeminderGoal, Datapoint, Contract, BeeminderUser

logger = getLogger(__name__)

try:
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("beeminder")

    client = BeeminderAPI(
        api_key=os.getenv("BEEMINDER_API_KEY"),
        default_user=os.getenv("BEEMINDER_USERNAME"),
    )

    logger.info("Successfully initialized FastMCP and Beeminder client")
except Exception as e:
    logger.error(f"Error during initialization: {str(e)}", exc_info=True)
    raise


@mcp.tool()
def get_goal(
    goal_slug: str,
    datapoints: bool = False,
    username: Optional[str] = os.getenv("BEEMINDER_USERNAME"),
) -> str:
    """Get information about a specific goal and return a BeeminderGoal instance.

    Args:
        user (Optional[str]): The Beeminder username. If None, use default_user.
        goal_slug (str): The slug identifier for the goal.
        datapoints (bool): Whether to include datapoints in the response.

    Returns:
        str: A JSON string representation of the BeeminderGoal instance.
    """
    try:
        goal = client.get_goal(goal_slug, username=username, datapoints=datapoints)
        return goal.model_dump_json()
    except Exception as e:
        logger.error(f"Error in get_goal: {str(e)}", exc_info=True)
        return f"Error retrieving settings: {str(e)}"


if __name__ == "__main__":
    try:
        logger.info("Starting server...")
        mcp.run(transport="stdio")
    except Exception as e:
        logger.error(f"Error running server: {str(e)}", exc_info=True)
        raise
