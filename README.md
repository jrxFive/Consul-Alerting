# Consul Alerting
A set of python files for Consul for checks, watches, and notifications. By using tags for services and checks,
consulalerting will notify the corresponding groups by whichever plugins are also in the tags list. For example
the redis service has plugins enabled for "hipchat" and will route notifications via hipchat to "devops" and "techops".
These routes are defined in the Consul KV under alerting/notify/, and can be setup using ConsulAlertingKVBoostrap.py, Consul KV, or programatically.


# Using Tags to notify

```javascript
{
  "service": {
    "name": "redis",
    "tags": ["devops","master","hipchat","dev"],
    "port": 8000,
    "check": {
      "script": "/usr/local/bin/check_redis.py",
      "interval": "10s"
    }
  }
}
```

# Install steps

```bash
git clone https://github.com/jrxFive/Consul-Alerting
cp -r Consul-Alerting/consulalerting <DESTINATION_FOLDER>
# edit ConsulAlertingKVBoostrap.py or setup manually on ConsulKV interface
python Consul-Alerting/ConsulAlertingKVBoostrap.py
```

After installing consulalerting in a directory of your choosing, use/edit ConsulAlertingKVBootstrap.py to ensure
the scripts can obtain the necessary KV information from Consul.

## Example ConsulAlertingKVBoostrap.py
```python




blacklist_nodes = ["fqdn","other_fqdn"]
blacklist_services = ["redis"]
blacklist_checks = ["service:redis"]

health_check_tags = ["devops","hipchat","techops"]

notify_hipchat= {"api_token":"",
                 "url":"https://api.hipchat.com/v1/rooms/message",
                 "rooms":{"devops":3},
                        {"techops":4},
                 }

notify_slack= {"api_token":"",
                 "rooms":{"techops":"#techops"}}

notify_mailgun= {"api_token":"",
                 "mailgun_domain":"",
                 "from": "consul@domain.com",
                 "teams":{"devops":["guy@example.com","girl@example.com"],
                          "qa": "lonelyqa@example.com"}
                 }

notify_email= {"mail_domain_address":"email.domain.com",
               "username":"",
               "password":"",
               "from": "consul@domain.com",
               "teams":{"devops":["guy@example.com","girl@example.com"],
                          "qa": "lonelyqa@example.com"}
                }

notify_pagerduty = {"teams":{
                             "devops":"<SERVICE_KEY>"
                             }
                   }
}

```

| Variable Name | Type | Description |
| ------------- |------------- | ----- |
| blacklist_nodes | List | Consul agents are not to notify of state changes, by "Node" name in /v1/health/node/<node> |
| blacklist_services | List | Consul agents are not to notify of particular services, by "ServiceName" in /v1/health/node/<node> |
| blacklist_checks | List | Consul agents are not to notify based on checks, by "CheckID" in  /v1/health/node/<node> |
| health_check_tags | List | Tags to be used to determine who to alert to and what type of alerts for non-application checks |





After the script is run, you can always change these within the Consul UI

## Consul Watch Check Handler Setup
```javascript
{
  "watches": [
    {
      "type": "checks",
      "handler": "<DESTINATION_FOLDER>/consulalerting/WatchCheckHandler.py"
    }
  ]
}
```

# Plugins

### Hipchat

| Keyname | Type | Description |
| ------- | ---- | ----------- |
| api_token | string | Hipchat requires an auth_token |
| url | string | URL address of API access for corresponding token |
| rooms | dict | Create dictionaries within 'rooms' for tags corresponding to hipchat rooms |

### Slack

| Keyname | Type | Description |
| ------- | ---- | ----------- |
| api_token | string | Slack requires an auth_token |
| rooms | dict | Create dictionaries within 'rooms' for tags corresponding to slack channels |

### Mailgun

| Keyname | Type | Description |
| ------- | ---- | ----------- |
| api_token | string | Mailgun requires an auth_token |
| mailgun_domain | string | Mailgun domain address  |
| from | string | From address when receiving an email |
| teams | dict | Create dictionaries within 'teams' for tags corresponding to teams or individuals |

### Email

| Keyname | Type | Description |
| ------- | ---- | ----------- |
| mail_domain_address | string | Email SMTP server to route alert |
| username | string | If the email SMTP server requires authentication |
| password | string | If the email SMTP server requires authentication |
| from | string | From address when receiving an email |
| teams | dict | Create dictionaries within 'teams' for tags corresponding to teams or individuals |


### Pagerduty

| Keyname | Type | Description |
| ------- | ---- | ----------- |
| teams | dict | Create dictionaries within 'teams' for tags corresponding to pagerduty teams, value is service_key |

# TODO
1. Logging
2. Improve performance additional profiling
3. Additional method documentation
3. Couple more plugins ~~(Pagerduty)~~ etc
4. Make it easier to add custom plugins
