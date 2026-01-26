
import asyncio
import httpx
import logging

async def test_bulk_load():
    url = "http://localhost:8000/api/leads/load"
    payload = {
        "location": "Novi",
        "specialty": "Family Medicine",
        "limit": 500
    }
    
    print(f"🚀 Testing Bulk Load for {payload['location']} (Limit: {payload['limit']})...")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("✅ Success!")
                print(response.json())
            else:
                print(f"❌ Failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_bulk_load())
