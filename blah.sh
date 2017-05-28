#!/bin/bash
# goobshots for Mac -- bind to a hotkey (Quicksilver works well)
# 5dbb7252f91979a155a659e351b886e0 is *your* key, test@example.com
echo -n | pbcopy
rm -f /tmp/x.png
screencapture -i -s /tmp/x.png
curl -T /tmp/x.png http://localhost:8080/put/5dbb7252f91979a155a659e351b886e0 | pbcopy
