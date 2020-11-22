#!/usr/bin/python3

import glob
import hashlib
import mmap
import os
from flask import Flask, request, Response
import gnupg

BASE_URL="https://tfregistry.power-devops.com"
KEYNAME="tfregistry.power-devops.com"
KEYEMAIL="info@power-devops.com"
PASSPHRASE="abc123"

class TFRegistry(Flask):
    def process_response(self, response):
        response.headers['Server'] = 'Terraform Simplistic Registry'
        return response

def sha256sum(filename):
    h  = hashlib.sha256()
    with open(filename, 'rb') as f:
        with mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ) as mm:
            h.update(mm)
    return h.hexdigest()

app = TFRegistry(__name__, static_folder='./static/', static_url_path='')
gpg = gnupg.GPG(gnupghome = './gpg')
gpginput = gpg.gen_key_input(key_type="RSA", subkey_type="RSA", expire_date=0, key_length=4096, name_real=KEYNAME, name_comment=KEYNAME, name_email=KEYEMAIL, passphrase=PASSPHRASE)
key = gpg.gen_key(gpginput)

@app.route('/v1/providers/<namespace>/<name>/versions')
def versions(namespace, name):
    providers = glob.glob("./static/%s/%s_*" % (namespace, name))
    if not providers:
        return {
            "errors": [
                "Not found"
            ]
        }, 404
    versions = []
    for filename in providers:
        # each provider has name provider_version_os_arch.zip
        provider = os.path.splitext(os.path.basename(filename))[0]
        info = provider.split('_')
        try:
            versions.append({
                "platforms": [
                    {
                        "arch": info[3],
                        "os": info[2],
                    },
                ],
                "protocols": [ "5.0" ],
                "version": info[1],
            })
        except:
            pass
    return {
        "id": "%s/%s" % (namespace, name),
        "versions": versions,
        "warnings": None,
    }

@app.route('/<namespace>/<name>_<version>_<os>_<arch>.zip_SHA256SUMS.sig')
def sha256sumssig(namespace, name, version, os, arch):
    filename = "%s_%s_%s_%s.zip" % (name, version, os, arch)
    sha = sha256sum("./static/%s/%s" % ( namespace, filename ) )
    content = "%s %s\n" % ( sha, filename )
    sig = gpg.sign(content, binary=True, detach=True, keyid=key.fingerprint, passphrase=PASSPHRASE)
    return Response(sig.data, mimetype="application/octet-stream")

@app.route('/<namespace>/<name>_<version>_<os>_<arch>.zip_SHA256SUMS')
def sha256sums(namespace, name, version, os, arch):
    filename = "%s_%s_%s_%s.zip" % (name, version, os, arch)
    sha = sha256sum("./static/%s/%s" % ( namespace, filename ) )
    return Response("%s %s\n" % ( sha, filename ), mimetype="application/octet-stream")

@app.route('/v1/providers/<namespace>/<name>/<version>/download/<os>/<arch>')
def download(namespace, name, version, os, arch):
    # real name to download is /<namespace>/<name>_<version>_<os>_<arch>.zip
    filename = "%s_%s_%s_%s.zip" % (name, version, os, arch)
    sha = sha256sum("./static/%s/%s" % ( namespace, filename ) )
    return {
        "arch": arch,
        "download_url": "%s/%s/%s" % ( BASE_URL, namespace, filename ),
        "filename": filename,
        "os": os,
        "protocols": [
            "5.0",
        ],
        "shasum": sha,
        "shasums_url": "%s/%s/%s_SHA256SUMS" % ( BASE_URL, namespace, filename ),
        "shasums_signature_url": "%s/%s/%s_SHA256SUMS.sig" % ( BASE_URL, namespace, filename ),
        "signing_keys": {
            "gpg_public_keys": [
                {
                    "key_id": key.fingerprint,
                    "ascii_armor": str(gpg.export_keys(key.fingerprint)),
                    "trust_signature": "",
                    "source": "",
                    "source_url": None,
                },
             ],
        },
    }


app.run(port=8000)
