# queryTicket
A script that retrieves a support ticket data from SalesForce

### Requirements
- You will need to generate an API token for your account in SalesForce
- The script expects the token and the user password to be stored and retrieved using [keyring](https://pypi.org/project/keyring/) (supports Keychain as a backend on OSX)

```
$ python3 queryTicket.py 
usage: queryTicket.py [-h] [--order O] [--num N] T
queryTicket.py: error: the following arguments are required: T
```
