# Portal Backend

## Testing Authenticated Endpoints

We currently use Auth0 for user authentication. Navigate to the Auth0 dashboard and sign-in with the Bitwarden credentials (not gmail SSO, this will give you the wrong account).

Navigate to `APIs > hackathon > Test`. Make sure to select `hackathon (Test Application)` for the application to test. Follow the instructions to generate a bearer token.

```
curl --request POST \
  --url "<domain>" \
  --header 'content-type: application/json' \
  --data '{
    "client_id":"<client_id>",
    "client_secret":"<client_secret>",
    "audience":"<audience>",
    "grant_type":"client_credentials"
  }'
```

Use the token with an Authorization Header to make an authorized request to the API.

```
curl --request GET \
  --url http://localhost:8000/<endpoint> \
  --header 'authorization: Bearer <token>`
```
