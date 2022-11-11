# Events Prediction Game
written in Python on Flask framework stolen without shame and updated from some
code a colleague left behind.

## Configurations
All configuration is currently stored inside the src/config/config.cfg file.
You can see a sample stored there for yourself, each value is overrideable via
environment variables to allow some form of security when pushing configurations
around.

### Events
The Application requires data from a sports API to keep it up to date and allow
for different events

### Sponsers
Should a sponser be running this event you can add their logo and name to be given
recognition for their work in the event's instance.

### CSS
The CSS stylesheet can be updated either with the APP_CSS environment variable
or within the config file under 'flask' section and 'css_file' heading. The name
of the CSS file must be added to 'src/static/css/' to be found by the application.

## Sports API
The API key from a sports/results providing API will be required to be stored in
the configuration file or via Environment Variable

## OAuth
This platform has tried to use all open libraries to enable up to date processing
of openid tokens. It should be as simple as adding a '<provider>_login' heading
to the configuration with the required variables to form an OAuth client, these can
be overrided with environment variables when required too in the format
'PROVIDER_VARIABLE_TO_OVERRIDE'.

## Databases
Database interaction happens through sqalchemy to provider connection to a database,
you will need to provide a sqalchemy connection string in the format of:

 <engine>://<username>:<password>@<database_address>:<database_port>/<database_name>

For example:
 mysql://root:root@127.0.0.1:3307/test_db

This Database will have to already exist before running the application but the tables
will be created automatically if they do not already exist.
