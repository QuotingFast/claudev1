# PlayAI Lead Connector

A middleware service that connects your lead generation platform to PlayAI for automated calling.

## Setup

1. Clone this repository
2. Run `npm install`
3. Run `node index.js` to start the server

## How it works

This service provides an API endpoint that Zapier can call when a new lead is generated. The service then triggers a call via the PlayAI API.
