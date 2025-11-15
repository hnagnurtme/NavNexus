using System;
using System.Threading;
using Neo4j.Driver;

namespace NavNexus.Infrastructure.Persistence;

/// <summary>
/// Lazy Neo4j connection wrapper. The driver is created on first use so
/// that the application startup doesn't fail when Neo4j is not yet available
/// (important when starting services with Docker Compose).
/// </summary>
public class Neo4jConnection : IDisposable
{
    private readonly string _uri;
    private readonly string _username;
    private readonly string _password;
    private IDriver? _driver;
    private readonly object _lock = new();

    public Neo4jConnection(string uri, string username, string password)
    {
        _uri = uri;
        _username = username;
        _password = password;
        _driver = null; // don't create driver here
    }

    private void EnsureDriver()
    {
        if (_driver is not null) return;

        lock (_lock)
        {
            if (_driver is not null) return;
            // Initialize the driver lazily with retry logic. Any exception here
            // will surface when the first DB operation occurs, but we attempt a
            // few retries to tolerate DB startup delays inside Docker Compose.
            const int maxAttempts = 5;
            int attempt = 0;
            Exception? lastEx = null;

            while (attempt < maxAttempts)
            {
                attempt++;
                try
                {
                    _driver = GraphDatabase.Driver(_uri, AuthTokens.Basic(_username, _password));
                    // Verify connectivity synchronously to ensure credentials/connection are valid.
                    _driver.VerifyConnectivityAsync().GetAwaiter().GetResult();
                    lastEx = null;
                    break;
                }
                catch (Exception ex)
                {
                    lastEx = ex;
                    // wait with simple backoff before retrying
                    Thread.Sleep(1000 * attempt);
                }
            }

            if (_driver is null && lastEx is not null)
            {
                // If all attempts failed, rethrow the last exception so callers can handle it.
                throw lastEx;
            }
        }
    }

    public IAsyncSession GetAsyncSession()
    {
        EnsureDriver();
        return _driver!.AsyncSession();
    }

    public void Dispose()
    {
        try
        {
            _driver?.Dispose();
        }
        catch
        {
            // Swallow dispose exceptions to avoid throwing from finalizers/DI teardown.
        }
    }
}
