#!/usr/bin/env python3
"""WebSocket client for Databricks App /logz/stream endpoint."""

import asyncio
import json
import os
import subprocess

import websockets
from dotenv import load_dotenv

# Load environment variables from .env.local
load_dotenv('.env.local')


class LogzWebSocketClient:
  """WebSocket client for streaming logs from Databricks App /logz/stream endpoint."""

  def __init__(self, app_url: str):
    self.app_url = app_url.rstrip('/')
    self.ws_url = (
      self.app_url.replace('https://', 'wss://').replace('http://', 'ws://') + '/logz/stream'
    )
    self._token_cache = None

  def _get_oauth_token(self) -> str:
    """Get OAuth token using Databricks CLI."""
    try:
      profile = os.getenv('DATABRICKS_CONFIG_PROFILE')
      host = os.getenv('DATABRICKS_HOST')

      cmd = ['databricks', 'auth', 'token']

      if profile:
        cmd.extend(['--profile', profile])
      elif host:
        cmd.extend(['--host', host])
      else:
        raise Exception(
          'Neither DATABRICKS_CONFIG_PROFILE nor DATABRICKS_HOST environment variable is set'
        )

      result = subprocess.run(cmd, capture_output=True, text=True, check=True)

      token_output = result.stdout.strip()
      try:
        token_data = json.loads(token_output)
        return token_data.get('access_token', token_output)
      except json.JSONDecodeError:
        return token_output

    except subprocess.CalledProcessError as e:
      raise Exception(f'Failed to get OAuth token: {e}')
    except FileNotFoundError:
      raise Exception('databricks CLI not found. Please install databricks CLI.')

  def _get_headers(self) -> dict:
    """Get WebSocket headers with authentication."""
    if not self._token_cache:
      self._token_cache = self._get_oauth_token()

    return {
      'Authorization': f'Bearer {self._token_cache}',
      'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
      'Origin': self.app_url,
      'Cookie': f'databricks-app-token={self._token_cache}',
    }

  async def stream_logs(self, search_query: str = '', duration: int = 30):
    """Stream logs from the WebSocket endpoint.

    Args:
        search_query: Optional search query to filter logs
        duration: How long to stream logs in seconds
    """
    headers = self._get_headers()

    print(f'Connecting to: {self.ws_url}')
    print(f"Search query: '{search_query}'")
    print(f'Streaming for {duration} seconds...')
    print('-' * 50)

    try:
      async with websockets.connect(
        self.ws_url, additional_headers=headers, ping_interval=20, ping_timeout=10
      ) as websocket:
        print('✅ WebSocket connected successfully!')

        # Send search query (always send, empty string for no filter)
        await websocket.send(search_query)
        if search_query:
          print(f"📤 Sent search query: '{search_query}'")
        else:
          print('📤 Sent empty search query (no filter)')

        # Stream logs for specified duration
        try:
          async with asyncio.timeout(duration):
            async for message in websocket:
              print(f'📋 {message}')
        except asyncio.TimeoutError:
          print(f'\n⏰ Streaming completed after {duration} seconds')

    except Exception as e:
      if 'websocket' in str(type(e)).lower():
        print(f'❌ WebSocket error: {e}')
      else:
        print(f'❌ Connection error: {e}')


async def main():
  """CLI interface for the logz WebSocket client."""
  import argparse

  parser = argparse.ArgumentParser(
    description='WebSocket client for Databricks App /logz/stream endpoint'
  )
  parser.add_argument('app_url', help='Base URL of the Databricks app')
  parser.add_argument('--search', default='', help='Search query to filter logs')
  parser.add_argument('--duration', type=int, default=30, help='How long to stream logs (seconds)')

  args = parser.parse_args()

  client = LogzWebSocketClient(args.app_url)
  await client.stream_logs(args.search, args.duration)


if __name__ == '__main__':
  asyncio.run(main())