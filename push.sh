#!/bin/bash
TOKEN=$1
git remote remove origin 2>/dev/null
git remote add origin https://$TOKEN@github.com/mdemonff10106-design/telegram-bot.git
git push -u origin main
