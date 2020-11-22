# Terraform Simplistic Registry

This is a very simplistic private registry for terraform providers. It can do just one thing:
let you download your provider.

## Prerequisites

* Python3 (tested with 3.6.8)
* pip3

## Installation

Install the required python packages:

```
# pip3 install flask
# pip3 install python-gnupg
```

Clone the repository:

```
git clone https://github.com/power-devops/tfregistry.git
```

## Configuration

In the beginning of main.py you will find several variables, you want to change:

```
BASE_URL="https://tfregistry.power-devops.com"
KEYNAME="tfregistry.power-devops.com"
KEYEMAIL="info@power-devops.com"
PASSPHRASE="abc123"
```

I recommend to set up a reverse proxy before the registry. For Apache HTTPd it is just one string:

```
ProxyPass "/" "http://127.0.0.1:8000/"
```

## Starting

If you use Linux with systemd, I recommend to copy tfregistry.service to /etc/systemd/system/ and run tfregistry as a service:

```
# cp tfregistry.service /etc/systemd/system/
# systemctl daemon-reload
# systemctl enable tfregistry
# systemctl start tfregistry
```

Don't forget to change the path in tfregistry.service.

If you don't use systemd, the start is very simple:

```
# python3 main.py
```

## Running

Now you have to decide, in which namespace you want to host your provider. According to Terraform documentation, the path to the provider
must be "namespace/provider" or "server/namespace/provider". Let's say your namespace is called *mynamespace* and the provider is *myprovider*.
It means you must first create namespace directory for you provider in the **static** subdirectory.

```
# mkdir static/mynamespace
```

You pack your provider using zip and put it into the namespace directory. Your zip archive's name must be made according to the following rule:

myprovidername_version_os_arch.zip

E.g.:

```
myprovider_0.0.1_darwin_amd64.zip
```

Now you can write in your terraform configuration:

```
terraform {
  required_providers {
    myprovider = {
      source = "tfregistry.example.com/mynamespace/myprovider"
      version = "0.0.1"
    }
  }
}
```

and it should work.

# Have fun!
