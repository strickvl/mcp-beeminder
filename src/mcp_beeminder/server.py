import os
from logging import getLogger
from typing import Optional, Dict, Any, List
import json

from beeminder_client.beeminder import BeeminderAPI

logger = getLogger(__name__)

INSTRUCTIONS = """
You are a helpful assistant that understands and helps with Beeminder goals. You understand both the technical mechanics and philosophical underpinnings of the system.

FUNDAMENTAL DEFINITION:
Beeminder is a tool for overcoming akrasia (acting against your better judgment) by combining:
- Quantified self-tracking
- Visual feedback via a "Bright Red Line" (BRL) showing your commitment path
- Financial stakes that increase with each failure
- Flexible commitment with a 7-day "akrasia horizon"

CORE PRINCIPLES:

1. Quantifiability:
   - ALL goals MUST be measurable/quantifiable
   - Data must be objective and verifiable
   - "If you can quantify it, you can beemind it"
   - Even qualitative goals must be transformed into measurable metrics
   - Example: "be nicer" → "give two compliments per day"

2. Goal Types:
   - Do More: accumulate value over time (e.g., study hours, workouts)
   - Do Less: stay under a limit (e.g., coffee intake, social media)
   - Whittle Down: reduce something over time (e.g., weight, inbox)
   - Odometer: cumulative tracking with resets (e.g., pages read across books)
   - Custom: any other quantifiable metric

3. The Bright Red Line (BRL):
   - Visual representation of your commitment
   - Shows minimum required progress over time
   - Components:
     * Rate: how fast you're committing to progress
     * Safety Buffer: cushion before derailment
     * Goal Value/Date: target endpoint (if applicable)
   - Derailment occurs when datapoint falls below BRL

4. Financial Stakes:
   - Standard Pledge Progression:
     * $0 → $5 → $10 → $30 → $90 → $270 → $810 → $2430 → $7290
   - Starting Options:
     * $0 ("feet wet" period, auto-increases to $5 after 7 days)
     * $5 (standard start)
   - Pledge Mechanics:
     * Pay current pledge amount upon derailment
     * Pledge automatically increases to next level (up to cap)
     * Can decrease pledge with 7-day wait
     * Immediate increases only with Beemium plan
     * No custom pledge amounts (must follow progression)
   - Pledge Cap:
     * User-defined maximum pledge level
     * Adjustable with 7-day wait
     * Derailments at cap don't increase further

5. Time Concepts:
   - Akrasia Horizon: 7-day delay on goal changes
   - Safe Days: buffer before next required datapoint
   - Beemergency: when you must enter data today
   - Initial Week: goal deletable without consequence
   - Midnight Deadline: cutoff for daily data

IMPLEMENTATION GUIDELINES:

1. Goal Creation Best Practices:
   - Ensure clear, measurable success criteria
   - Start with conservative rates
   - Build in buffer for unexpected events
   - Consider automated tracking options
   - Set appropriate initial safety buffer
   - Choose pledge cap thoughtfully
   - Start with $0-$5 pledges while learning

2. Data Management:
   - Regular updates preferred (daily if possible)
   - Multiple datapoints allowed
   - Supports various formats (HH:MM, dates)
   - Auto-summing where appropriate
   - Careful timezone handling
   - Ratcheting available to reduce buffer

3. Common Failure Points to Avoid:
   - Non-quantifiable metrics
   - Unrealistic rates
   - Insufficient safety buffer
   - Overcomplicated tracking
   - Conflicting goals
   - Ignoring timezone boundaries
   - Missing emergency buffer

4. Emergency Handling:
   - Break options (with 7-day notice)
   - Legitimate derailment process
   - Payment failure procedures
   - Illness/travel accommodations
   - Data error corrections

WHEN ADVISING USERS:

1. Assessment Checklist:
   - Goal quantifiability
   - Rate sustainability
   - Tracking feasibility
   - Buffer adequacy
   - Pledge appropriateness

2. Response Structure:
   - Confirm goal understanding
   - Verify quantifiability
   - Suggest tracking method
   - Identify potential pitfalls
   - Recommend safety measures
   - Outline success metrics

3. Key Reminders:
   - All changes have 7-day delay
   - Always maintain safety buffer
   - Regular data entry crucial
   - Pledge increases automatic
   - Consider emergency scenarios

Remember: Beeminder combines meaningful commitment with maximal flexibility,
designed to help users achieve their goals while maintaining accountability.

Responses to queries should include tables where appropriate to better present
information to the user.
"""

try:
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP(name="beeminder", instructions=INSTRUCTIONS)

    client = BeeminderAPI(
        api_key=os.getenv("BEEMINDER_API_KEY"),
        default_user=os.getenv("BEEMINDER_USERNAME"),
    )

    logger.info("Successfully initialized FastMCP and Beeminder client")
except Exception as e:
    logger.error(f"Error during initialization: {str(e)}", exc_info=True)
    raise


@mcp.tool(description="Returns information about a specific goal.")
def get_goal(
    goal_slug: str,
    datapoints: bool = False,
) -> str:
    """Get information about a specific goal and return a BeeminderGoal instance.

    Args:
        goal_slug (str): The slug identifier for the goal.
        datapoints (bool): Whether to include datapoints in the response.

    Returns:
        str: A JSON string representation of the BeeminderGoal instance.
    """
    try:
        goal = client.get_goal(
            goal_slug=goal_slug,
            datapoints=datapoints,
            user=client.default_user,
        )
        return goal.model_dump_json()
    except Exception as e:
        logger.error(f"Error in get_goal: {str(e)}", exc_info=True)
        return f"Error retrieving settings: {str(e)}"


@mcp.tool(
    description="Returns all goals for the current user that is best presented in a table."
)
def list_goals() -> str:
    """List all goals for the current user.

    Returns:
        str: A JSON string representation of the list of BeeminderGoal instances.
    """
    try:
        goals = client.get_all_goals(user=client.default_user)
        return json.dumps([goal.model_dump() for goal in goals])
    except Exception as e:
        logger.error(f"Error in list_goals: {str(e)}", exc_info=True)
        return f"Error retrieving goals: {str(e)}"


@mcp.tool(
    description="Returns all archived goals for the current user that is best presented in a table."
)
def get_archived_goals() -> str:
    """Get all archived goals for the current user.

    Returns:
        str: A JSON string representation of the list of archived BeeminderGoal instances.
    """
    try:
        goals = client.get_archived_goals(user=client.default_user)
        return json.dumps([goal.model_dump() for goal in goals])
    except Exception as e:
        logger.error(f"Error in get_archived_goals: {str(e)}", exc_info=True)
        return f"Error retrieving archived goals: {str(e)}"


@mcp.tool(
    description="""Creates a new Beeminder goal. The data required to create the goal, which may include:
    - slug: The URL slug for the goal
    - title: The display title for the goal 
    - goal_type: The type of goal (do_more, do_less, whittle_down, etc.)
    - goalval: The target value for the goal
    - rate: The rate at which to progress towards the goal
    - runits: The units for the goal (e.g., 'hours', 'pages', 'kg')
    And any other valid goal parameters
    Note that exactly two out of three of goaldate, goalval, and rate are required."""
)
def create_goal(
    goal_data: Dict[str, Any],
) -> str:
    """Create a new Beeminder goal.

    Args:
        goal_data (Dict[str, Any]): The data required to create the goal, which may include:
            - slug: The URL slug for the goal
            - title: The display title for the goal
            - goal_type: The type of goal (do_more, do_less, whittle_down, etc.)
            - goalval: The target value for the goal
            - rate: The rate at which to progress towards the goal
            - runits: The units for the goal (e.g., "hours", "pages", "kg")
            And any other valid goal parameters

            Note that exactly two out of three of goaldate, goalval, and rate
            are required.

    A Goal object includes everything about a specific goal for a specific user, including the target value and date, the steepness of the bright red line, the graph image, and various settings for the goal.

    Other important information about a goal includes:

    slug (string): The final part of the URL of the goal, used as an identifier. E.g., if user "alice" has a goal at beeminder.com/alice/weight then the goal's slug is "weight".
    updated_at (number): Unix timestamp of the last time this goal was updated.
    title (string): The title that the user specified for the goal. E.g., "Weight Loss".
    fineprint (string): The user-provided description of what exactly they are committing to.
    yaxis (string): The label for the y-axis of the graph. E.g., "Cumulative total hours".
    goaldate (number): Unix timestamp (in seconds) of the goal date. NOTE: this may be null; see below.
    goalval (number): Goal value — the number the bright red line will eventually reach. E.g., 70 kilograms. NOTE: this may be null; see below.
    rate (number): The slope of the (final section of the) bright red line. You must also consider runits to fully specify the rate. NOTE: this may be null; see below.
    runits (string): Rate units. One of y, m, w, d, h indicating that the rate of the bright red line is yearly, monthly, weekly, daily, or hourly.
    svg_url (string): URL for the goal's graph svg. E.g., "http://static.beeminder.com/alice/weight.svg".
    graph_url (string): URL for the goal's graph image. E.g., "http://static.beeminder.com/alice/weight.png".
    thumb_url (string): URL for the goal's graph thumbnail image. E.g., "http://static.beeminder.com/alice/weight-thumb.png".
    autodata (string): The name of automatic data source, if this goal has one. Will be null for manual goals.
    goal_type (string): One of the following symbols (detailed info below):
        hustler: Do More
        biker: Odometer
        fatloser: Weight loss
        gainer: Gain Weight
        inboxer: Inbox Fewer
        drinker: Do Less
    custom: Full access to the underlying goal parameters
    losedate (number): Unix timestamp of derailment. When you'll cross the bright red line if nothing is reported.
    urgencykey (string): Sort by this key to put the goals in order of decreasing urgency. (Case-sensitive ascii or unicode sorting is assumed). This is the order the goals list comes in. Detailed info on the blog.
    queued (boolean): Whether the graph is currently being updated to reflect new data.
    secret (boolean): Whether you have to be logged in as owner of the goal to view it. Default: false.
    datapublic (boolean): Whether you have to be logged in as the owner of the goal to view the datapoints. Default: false.
    datapoints (array of Datapoints): The datapoints for this goal.
    numpts (number): Number of datapoints.
    pledge (number): Amount pledged (USD) on the goal.
    initday (number): Unix timestamp (in seconds) of the start of the bright red line.
    initval (number): The y-value of the start of the bright red line.
    curday (number): Unix timestamp (in seconds) of the end of the bright red line, i.e., the most recent (inferred) datapoint.
    curval (number): The value of the most recent datapoint.
    currate (number): The rate of the red line at time curday; if there's a rate change on that day, take the limit from the left.
    lastday (number): Unix timestamp (in seconds) of the last (explicitly entered) datapoint.
    yaw (number): Good side of the bright red line. I.e., the side of the line (+1/-1 = above/below) that makes you say "yay".
    dir (number): Direction the bright red line is sloping, usually the same as yaw.
    lane (number): Deprecated. See losedate and safebuf.
    mathishard (array of 3 numbers): The goaldate, goalval, and rate — all filled in. (The commitment dial specifies 2 out of 3 and you can check this if you want Beeminder to do the math for you on inferring the third one.) Note: this field may be null if the goal is in an error state such that the graph image can't be generated.
    headsum (string): Deprecated. Summary text blurb saying how much safety buffer you have.
    limsum (string): Summary of what you need to do to eke by, e.g., "+2 within 1 day".
    kyoom (boolean): Cumulative; plot values as the sum of all those entered so far, aka auto-summing.
    odom (boolean): Treat zeros as accidental odometer resets.
    aggday (string): How to aggregate points on the same day, eg, min/max/mean.
    steppy (boolean): Join dots with purple steppy-style line.
    rosy (boolean): Show the rose-colored dots and connecting line.
    movingav (boolean): Show moving average line superimposed on the data.
    aura (boolean): Show turquoise swath, aka blue-green aura.
    frozen (boolean): Whether the goal is currently frozen and therefore must be restarted before continuing to accept data.
    won (boolean): Whether the goal has been successfully completed.
    lost (boolean): Whether the goal is currently off track.
    maxflux (Integer): Max daily fluctuation for weight goals. Used as an absolute buffer amount after a derail. Also shown on the graph as a thick guiding line.
    contract (dictionary): Dictionary with two attributes. amount is the amount at risk on the contract, and stepdown_at is a Unix timestamp of when the contract is scheduled to revert to the next lowest pledge amount. null indicates that it is not scheduled to revert.
    road (array): Array of tuples that can be used to construct the Bright Red Line (formerly "Yellow Brick Road"). This field is also known as the graph matrix. Each tuple specifies 2 out of 3 of [time, goal, rate]. To construct road, start with a known starting point (time, value) and then each row of the graph matrix specifies 2 out of 3 of {t,v,r} which gives the segment ending at time t. You can walk forward filling in the missing 1-out-of-3 from the (time, value) in the previous row.
    roadall (array): Like road but with an additional initial row consisting of [initday, initval, null] and an additional final row consisting of [goaldate, goalval, rate].
    fullroad (array): Like roadall but with the nulls filled in.
    rah (number): Red line value (y-value of the bright red line) at the akrasia horizon (today plus one week).
    delta (number): Distance from the bright red line to today's datapoint (curval).
    delta_text (string): Deprecated.
    safebuf (number): The integer number of safe days. If it's a beemergency this will be zero.
    safebump (number): The absolute y-axis number you need to reach to get one additional day of safety buffer.
    autoratchet (number): The goal's autoratchet setting. If it's not set or they don't have permission to autoratchet, its value will be nil. This represents the maximum number of days of safety buffer the goal is allowed to accrue, or in the case of a Do-Less goal, the max buffer in terms of the goal's units. Read-only.
    id (string of hex digits): We prefer using user/slug as the goal identifier, however, since we began allowing users to change slugs, this id is useful!
    callback_url (string): Callback URL, as discussed in the forum. WARNING: If different apps change this they'll step on each other's toes.
    description (string): Deprecated. User-supplied description of goal (listed in sidebar of graph page as "Goal Statement").
    graphsum (string): Deprecated. Text summary of the graph, not used in the web UI anymore.
    lanewidth (number): Deprecated. Now always zero.
    deadline (number): Seconds by which your deadline differs from midnight. Negative is before midnight, positive is after midnight. Allowed range is -17*3600 to 6*3600 (7am to 6am).
    leadtime (number): Days before derailing we start sending you reminders. Zero means we start sending them on the beemergency day, when you will derail later that day.
    alertstart (number): Seconds after midnight that we start sending you reminders (on the day that you're scheduled to start getting them, see leadtime above).
    plotall (boolean): Whether to plot all the datapoints, or only the aggday'd one. So if false then only the official datapoint that's counted is plotted.
    last_datapoint (Datapoint): The last datapoint entered for this goal.
    integery (boolean): Assume that the units must be integer values. Used for things like limsum.
    gunits (string): Goal units, like "hours" or "pushups" or "pages".
    hhmmformat (boolean): Whether to show data in a "timey" way, with colons. For example, this would make a 1.5 show up as 1:30.
    todayta (boolean): Whether there are any datapoints for today
    weekends_off (boolean): If the goal has weekends automatically scheduled.
    tmin (string): Lower bound on x-axis; don't show data before this date; using yyyy-mm-dd date format. (In Graph Settings this is 'X-min')
    tmax (string): Upper bound on x-axis; don't show data after this date; using yyyy-mm-dd date format. (In Graph Settings this is 'X-max')
    tags (array): A list of the goal's tags.
    A note about rate, date, and val: One of the three fields goaldate, goalval, and rate will return a null value. This indicates that the value is calculated based on the other two fields, as selected by the user.

    A detailed note about goal types: The goal types are shorthand for a collection of settings of more fundamental goal attributes. Note that changing the goal type of an already-created goal has no effect on those fundamental goal attributes. The following table lists what those attributes are.

    parameter	hustler	biker	fatloser	gainer	inboxer	drinker
    yaw	1	1	-1	1	-1	-1
    dir	1	1	-1	1	-1	1
    kyoom	true	false	false	false	false	true
    odom	false	true	false	false	false	false
    edgy	false	false	false	false	false	true
    aggday	"sum"	"last"	"min"	"max"	"min"	"sum"
    steppy	true	true	false	false	true	true
    rosy	false	false	true	true	false	false
    movingav	false	false	true	true	false	false
    aura	false	false	true	true	false	false
    There are four broad, theoretical categories — called the platonic goal types — that goals fall into, defined by dir and yaw:

    MOAR = dir +1 & yaw +1: "go up, like work out more"
    PHAT = dir -1 & yaw -1: "go down, like weightloss or gmailzero"
    WEEN = dir +1 & yaw -1: "go up less, like quit smoking"
    RASH = dir -1 & yaw +1: "go down less, ie, rationing, for example"

    Returns:
        str: A JSON string representation of the created BeeminderGoal instance.
    """
    try:
        goal = client.create_goal(
            user=client.default_user,
            goal_data=goal_data,
        )
        return goal.model_dump_json()
    except Exception as e:
        logger.error(f"Error in create_goal: {str(e)}", exc_info=True)
        return f"Error creating goal: {str(e)}"


@mcp.tool(
    description="Returns all datapoints for a specific goal that is best presented in a table."
)
def get_datapoints(
    goal_slug: str,
    sort: Optional[str] = None,
    count: Optional[int] = None,
    page: Optional[int] = None,
    per: Optional[int] = None,
) -> str:
    """Get all datapoints for a specific goal.

    Note on datapoint data that you get back:
        id (string): A unique ID, used to identify a datapoint when deleting or editing it.
        timestamp (number): The unix time (in seconds) of the datapoint.
        daystamp (string): The date of the datapoint (e.g., "20150831"). Sometimes timestamps are surprising due to goal deadlines, so if you're looking at Beeminder data, you're probably interested in the daystamp.
        value (number): The value, e.g., how much you weighed on the day indicated by the timestamp.
        comment (string): An optional comment about the datapoint.
        updated_at (number): The unix time that this datapoint was entered or last updated.
        requestid (string): If a datapoint was created via the API and this parameter was included, it will be echoed back.
        origin (string): A short code related to where the datapoint came from. E.g. if it was added from the website, it would be "web"; if it was added by an autodata integration, e.g. Duolingo, it would be "duolingo".
        creator (string): Similar to origin, but for users. Especially in context of group goals, should resolve to the member who added the data, assuming the member is still around etc. When there isn't a logical creator this will be null.
        is_dummy (boolean): Not a logical datapoint, e.g. a "#DERAIL" datapoint, or Pessimistic Presumptive datapoint, added by Beeminder.
        is_initial (boolean): The initial datapoint added at goal creation time. Depending on the goal type this can be semantically slightly different from a "dummy" datapoint, e.g. in the case of an Odometer goal, it's a meaningful datapoint because it sets your starting count, which is "actual" data, and meaningful to the goal, but in the case of a Do More goal, it's more of a placeholder.
        created_at (time): This is the timestamp at which the datapoint was created, which may differ from the datapoint's timestamp because of Reasons.

    Args:
        goal_slug (str): The slug identifier for the goal.
        sort (Optional[str]): Attribute to sort on, descending. Defaults to id.
        count (Optional[int]): Limit results to count number of datapoints.
        page (Optional[int]): Page number for pagination (1-indexed).
        per (Optional[int]): Number of results per page. Default 25.

    Returns:
        str: A JSON string representation of the list of Datapoint instances.
    """
    try:
        datapoints = client.get_datapoints(
            user=client.default_user,
            goal_slug=goal_slug,
            sort=sort,
            count=count,
            page=page,
            per=per,
        )
        return json.dumps([datapoint.model_dump() for datapoint in datapoints])
    except Exception as e:
        logger.error(f"Error in get_datapoints: {str(e)}", exc_info=True)
        return f"Error retrieving datapoints: {str(e)}"


@mcp.tool(
    description="""Creates a new datapoint for a goal. The data required to create the datapoint, which may include:
    - goal_slug: The slug identifier for the goal
    - value: The value for the datapoint
    - timestamp: Unix timestamp for the datapoint
    - daystamp: Date stamp (YYYYMMDD format)
    - comment: Comment for the datapoint
    - requestid: Unique identifier for this datapoint"""
)
def create_datapoint(
    goal_slug: str,
    value: float,
    timestamp: Optional[int] = None,
    daystamp: Optional[str] = None,
    comment: Optional[str] = None,
    requestid: Optional[str] = None,
) -> str:
    """Create a new datapoint for a goal.

    Args:
        goal_slug (str): The slug identifier for the goal
        value (float): The value for the datapoint
        timestamp (Optional[int]): Unix timestamp for the datapoint
        daystamp (Optional[str]): Date stamp (YYYYMMDD format)
        comment (Optional[str]): Comment for the datapoint
        requestid (Optional[str]): Unique identifier for this datapoint

    Returns:
        str: A JSON string representation of the created Datapoint instance.
    """
    try:
        datapoint = client.create_datapoint(
            user=client.default_user,
            goal_slug=goal_slug,
            value=value,
            timestamp=timestamp,
            daystamp=daystamp,
            comment=comment,
            requestid=requestid,
        )
        return datapoint.model_dump_json()
    except Exception as e:
        logger.error(f"Error in create_datapoint: {str(e)}", exc_info=True)
        return f"Error creating datapoint: {str(e)}"


@mcp.tool(
    description="""Creates multiple datapoints for a goal. The data required to create the datapoints, which may include:
    - goal_slug: The slug identifier for the goal
    - datapoints: List of datapoint objects to create, each containing:
        - value: The value for the datapoint
        - timestamp: Unix timestamp
        - daystamp: Date stamp (YYYYMMDD)
        - comment: Comment - requestid: Unique identifier"""
)
def create_multiple_datapoints(
    goal_slug: str,
    datapoints: List[Dict[str, Any]],
) -> str:
    """Create multiple datapoints for a goal.

    Args:
        goal_slug (str): The slug identifier for the goal
        datapoints (List[Dict[str, Any]]): List of datapoint objects to create, each containing:
            - value (float): The value for the datapoint
            - timestamp (Optional[int]): Unix timestamp
            - daystamp (Optional[str]): Date stamp (YYYYMMDD)
            - comment (Optional[str]): Comment
            - requestid (Optional[str]): Unique identifier

    Returns:
        str: A JSON string representation of the response containing lists of successful and failed datapoints.
    """
    try:
        result = client.create_multiple_datapoints(
            user=client.default_user,
            goal_slug=goal_slug,
            datapoints=datapoints,
        )
        return json.dumps(result)
    except Exception as e:
        logger.error(f"Error in create_multiple_datapoints: {str(e)}", exc_info=True)
        return f"Error creating multiple datapoints: {str(e)}"


@mcp.tool(
    description="""Deletes a datapoint. The data required to delete the datapoint, which may include:
    - goal_slug: The slug identifier for the goal
    - datapoint_id: The ID of the datapoint to delete"""
)
def delete_datapoint(
    goal_slug: str,
    datapoint_id: str,
) -> str:
    """Delete a datapoint.

    Args:
        goal_slug (str): The slug identifier for the goal
        datapoint_id (str): The ID of the datapoint to delete

    Returns:
        str: A JSON string representation of the deleted Datapoint instance.
    """
    try:
        datapoint = client.delete_datapoint(
            user=client.default_user,
            goal_slug=goal_slug,
            datapoint_id=datapoint_id,
        )
        return datapoint.model_dump_json()
    except Exception as e:
        logger.error(f"Error in delete_datapoint: {str(e)}", exc_info=True)
        return f"Error deleting datapoint: {str(e)}"


@mcp.tool(description="Returns information about the current user.")
def get_user() -> str:
    """Get information about the current user.

    Returns:
        str: A JSON string representation of the BeeminderUser instance.
    """
    try:
        user = client.get_user(user=client.default_user)
        return user.model_dump_json()
    except Exception as e:
        logger.error(f"Error in get_user: {str(e)}", exc_info=True)
        return f"Error retrieving user: {str(e)}"


@mcp.tool(
    description="""Updates an existing Beeminder goal. The data required to update the goal, which may include:
    - goal_slug: The slug identifier for the goal
    - update_data: The data to update the goal with, which may include:
        - title: New title for the goal
        - rate: New rate for the goal
        - goalval: New target value
        - goal_type: New goal type - runits: New units And any other valid goal parameters"""
)
def update_goal(
    goal_slug: str,
    update_data: Dict[str, Any],
) -> str:
    """Update an existing Beeminder goal.

    Args:
        goal_slug (str): The slug identifier for the goal
        update_data (Dict[str, Any]): The data to update the goal with, which may include:
            - title (str): New title for the goal
            - rate (float): New rate for the goal
            - goalval (float): New target value
            - goal_type (str): New goal type
            - runits (str): New units
            And any other valid goal parameters

    A Goal object includes everything about a specific goal for a specific user, including the target value and date, the steepness of the bright red line, the graph image, and various settings for the goal.

    Other important information about a goal includes:

    slug (string): The final part of the URL of the goal, used as an identifier. E.g., if user "alice" has a goal at beeminder.com/alice/weight then the goal's slug is "weight".
    updated_at (number): Unix timestamp of the last time this goal was updated.
    title (string): The title that the user specified for the goal. E.g., "Weight Loss".
    fineprint (string): The user-provided description of what exactly they are committing to.
    yaxis (string): The label for the y-axis of the graph. E.g., "Cumulative total hours".
    goaldate (number): Unix timestamp (in seconds) of the goal date. NOTE: this may be null; see below.
    goalval (number): Goal value — the number the bright red line will eventually reach. E.g., 70 kilograms. NOTE: this may be null; see below.
    rate (number): The slope of the (final section of the) bright red line. You must also consider runits to fully specify the rate. NOTE: this may be null; see below.
    runits (string): Rate units. One of y, m, w, d, h indicating that the rate of the bright red line is yearly, monthly, weekly, daily, or hourly.
    svg_url (string): URL for the goal's graph svg. E.g., "http://static.beeminder.com/alice/weight.svg".
    graph_url (string): URL for the goal's graph image. E.g., "http://static.beeminder.com/alice/weight.png".
    thumb_url (string): URL for the goal's graph thumbnail image. E.g., "http://static.beeminder.com/alice/weight-thumb.png".
    autodata (string): The name of automatic data source, if this goal has one. Will be null for manual goals.
    goal_type (string): One of the following symbols (detailed info below):
        hustler: Do More
        biker: Odometer
        fatloser: Weight loss
        gainer: Gain Weight
        inboxer: Inbox Fewer
        drinker: Do Less
    custom: Full access to the underlying goal parameters
    losedate (number): Unix timestamp of derailment. When you'll cross the bright red line if nothing is reported.
    urgencykey (string): Sort by this key to put the goals in order of decreasing urgency. (Case-sensitive ascii or unicode sorting is assumed). This is the order the goals list comes in. Detailed info on the blog.
    queued (boolean): Whether the graph is currently being updated to reflect new data.
    secret (boolean): Whether you have to be logged in as owner of the goal to view it. Default: false.
    datapublic (boolean): Whether you have to be logged in as the owner of the goal to view the datapoints. Default: false.
    datapoints (array of Datapoints): The datapoints for this goal.
    numpts (number): Number of datapoints.
    pledge (number): Amount pledged (USD) on the goal.
    initday (number): Unix timestamp (in seconds) of the start of the bright red line.
    initval (number): The y-value of the start of the bright red line.
    curday (number): Unix timestamp (in seconds) of the end of the bright red line, i.e., the most recent (inferred) datapoint.
    curval (number): The value of the most recent datapoint.
    currate (number): The rate of the red line at time curday; if there's a rate change on that day, take the limit from the left.
    lastday (number): Unix timestamp (in seconds) of the last (explicitly entered) datapoint.
    yaw (number): Good side of the bright red line. I.e., the side of the line (+1/-1 = above/below) that makes you say "yay".
    dir (number): Direction the bright red line is sloping, usually the same as yaw.
    lane (number): Deprecated. See losedate and safebuf.
    mathishard (array of 3 numbers): The goaldate, goalval, and rate — all filled in. (The commitment dial specifies 2 out of 3 and you can check this if you want Beeminder to do the math for you on inferring the third one.) Note: this field may be null if the goal is in an error state such that the graph image can't be generated.
    headsum (string): Deprecated. Summary text blurb saying how much safety buffer you have.
    limsum (string): Summary of what you need to do to eke by, e.g., "+2 within 1 day".
    kyoom (boolean): Cumulative; plot values as the sum of all those entered so far, aka auto-summing.
    odom (boolean): Treat zeros as accidental odometer resets.
    aggday (string): How to aggregate points on the same day, eg, min/max/mean.
    steppy (boolean): Join dots with purple steppy-style line.
    rosy (boolean): Show the rose-colored dots and connecting line.
    movingav (boolean): Show moving average line superimposed on the data.
    aura (boolean): Show turquoise swath, aka blue-green aura.
    frozen (boolean): Whether the goal is currently frozen and therefore must be restarted before continuing to accept data.
    won (boolean): Whether the goal has been successfully completed.
    lost (boolean): Whether the goal is currently off track.
    maxflux (Integer): Max daily fluctuation for weight goals. Used as an absolute buffer amount after a derail. Also shown on the graph as a thick guiding line.
    contract (dictionary): Dictionary with two attributes. amount is the amount at risk on the contract, and stepdown_at is a Unix timestamp of when the contract is scheduled to revert to the next lowest pledge amount. null indicates that it is not scheduled to revert.
    road (array): Array of tuples that can be used to construct the Bright Red Line (formerly "Yellow Brick Road"). This field is also known as the graph matrix. Each tuple specifies 2 out of 3 of [time, goal, rate]. To construct road, start with a known starting point (time, value) and then each row of the graph matrix specifies 2 out of 3 of {t,v,r} which gives the segment ending at time t. You can walk forward filling in the missing 1-out-of-3 from the (time, value) in the previous row.
    roadall (array): Like road but with an additional initial row consisting of [initday, initval, null] and an additional final row consisting of [goaldate, goalval, rate].
    fullroad (array): Like roadall but with the nulls filled in.
    rah (number): Red line value (y-value of the bright red line) at the akrasia horizon (today plus one week).
    delta (number): Distance from the bright red line to today's datapoint (curval).
    delta_text (string): Deprecated.
    safebuf (number): The integer number of safe days. If it's a beemergency this will be zero.
    safebump (number): The absolute y-axis number you need to reach to get one additional day of safety buffer.
    autoratchet (number): The goal's autoratchet setting. If it's not set or they don't have permission to autoratchet, its value will be nil. This represents the maximum number of days of safety buffer the goal is allowed to accrue, or in the case of a Do-Less goal, the max buffer in terms of the goal's units. Read-only.
    id (string of hex digits): We prefer using user/slug as the goal identifier, however, since we began allowing users to change slugs, this id is useful!
    callback_url (string): Callback URL, as discussed in the forum. WARNING: If different apps change this they'll step on each other's toes.
    description (string): Deprecated. User-supplied description of goal (listed in sidebar of graph page as "Goal Statement").
    graphsum (string): Deprecated. Text summary of the graph, not used in the web UI anymore.
    lanewidth (number): Deprecated. Now always zero.
    deadline (number): Seconds by which your deadline differs from midnight. Negative is before midnight, positive is after midnight. Allowed range is -17*3600 to 6*3600 (7am to 6am).
    leadtime (number): Days before derailing we start sending you reminders. Zero means we start sending them on the beemergency day, when you will derail later that day.
    alertstart (number): Seconds after midnight that we start sending you reminders (on the day that you're scheduled to start getting them, see leadtime above).
    plotall (boolean): Whether to plot all the datapoints, or only the aggday'd one. So if false then only the official datapoint that's counted is plotted.
    last_datapoint (Datapoint): The last datapoint entered for this goal.
    integery (boolean): Assume that the units must be integer values. Used for things like limsum.
    gunits (string): Goal units, like "hours" or "pushups" or "pages".
    hhmmformat (boolean): Whether to show data in a "timey" way, with colons. For example, this would make a 1.5 show up as 1:30.
    todayta (boolean): Whether there are any datapoints for today
    weekends_off (boolean): If the goal has weekends automatically scheduled.
    tmin (string): Lower bound on x-axis; don't show data before this date; using yyyy-mm-dd date format. (In Graph Settings this is 'X-min')
    tmax (string): Upper bound on x-axis; don't show data after this date; using yyyy-mm-dd date format. (In Graph Settings this is 'X-max')
    tags (array): A list of the goal's tags.
    A note about rate, date, and val: One of the three fields goaldate, goalval, and rate will return a null value. This indicates that the value is calculated based on the other two fields, as selected by the user.

    A detailed note about goal types: The goal types are shorthand for a collection of settings of more fundamental goal attributes. Note that changing the goal type of an already-created goal has no effect on those fundamental goal attributes. The following table lists what those attributes are.

    parameter	hustler	biker	fatloser	gainer	inboxer	drinker
    yaw	1	1	-1	1	-1	-1
    dir	1	1	-1	1	-1	1
    kyoom	true	false	false	false	false	true
    odom	false	true	false	false	false	false
    edgy	false	false	false	false	false	true
    aggday	"sum"	"last"	"min"	"max"	"min"	"sum"
    steppy	true	true	false	false	true	true
    rosy	false	false	true	true	false	false
    movingav	false	false	true	true	false	false
    aura	false	false	true	true	false	false
    There are four broad, theoretical categories — called the platonic goal types — that goals fall into, defined by dir and yaw:

    MOAR = dir +1 & yaw +1: "go up, like work out more"
    PHAT = dir -1 & yaw -1: "go down, like weightloss or gmailzero"
    WEEN = dir +1 & yaw -1: "go up less, like quit smoking"
    RASH = dir -1 & yaw +1: "go down less, ie, rationing, for example"

    Returns:
        str: A JSON string representation of the updated BeeminderGoal instance.
    """
    try:
        result = client.update_goal(
            user=client.default_user,
            goal_slug=goal_slug,
            update_data=update_data,
        )
        return json.dumps(result)
    except Exception as e:
        logger.error(f"Error in update_goal: {str(e)}", exc_info=True)
        return f"Error updating goal: {str(e)}"


@mcp.tool(
    description="""Deletes a Beeminder goal. The data required to delete the goal, which may include:
    - goal_slug: The slug identifier for the goal"""
)
def delete_goal(goal_slug: str) -> str:
    """Delete a Beeminder goal.

    Args:
        goal_slug (str): The slug identifier for the goal

    Returns:
        str: Success or error message
    """
    try:
        client.delete_goal(user=client.default_user, goal_slug=goal_slug)
        return json.dumps({"status": "success", "message": "Goal deleted successfully"})
    except Exception as e:
        logger.error(f"Error in delete_goal: {str(e)}", exc_info=True)
        return json.dumps({"status": "error", "message": str(e)})


if __name__ == "__main__":
    try:
        logger.info("Starting server...")
        mcp.run(transport="stdio")
    except Exception as e:
        logger.error(f"Error running server: {str(e)}", exc_info=True)
        raise
