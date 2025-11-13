using Hangfire.Dashboard;

namespace NavNexus.API.Filters;

public class HangfireAuthorizationFilter : IDashboardAuthorizationFilter
{
    public bool Authorize(DashboardContext context)
    {
        // Allow access in development mode
        // In production, implement proper authorization
        return true;
    }
}
