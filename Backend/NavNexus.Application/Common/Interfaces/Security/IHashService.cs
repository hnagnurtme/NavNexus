namespace NavNexus.Application.Common.Interfaces.Security;
public interface IHashService
{
    string Hash(string input);
    bool Verify(string hash, string input);
}