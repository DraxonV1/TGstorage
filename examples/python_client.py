import httpx
import asyncio

# Configuration
API_BASE = "http://localhost"  # Change to your production URL
API_KEY = "your_secure_admin_key_here"

async def upload_file(file_path):
    async with httpx.AsyncClient(timeout=300) as client:
        files = {'file': open(file_path, 'rb')}
        headers = {'X-API-Key': API_KEY}
        
        print(f"Uploading {file_path}...")
        response = await client.post(f"{API_BASE}/upload", files=files, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Upload Success!")
            print(f"Direct Link: {data['direct_link']}")
            print(f"Share Link:  {data['share_link']}")
            return data
        else:
            print(f"✗ Upload Failed: {response.status_code}")
            print(response.text)
            return None

async def list_files():
    async with httpx.AsyncClient() as client:
        headers = {'X-API-Key': API_KEY}
        response = await client.get(f"{API_BASE}/files", headers=headers)
        if response.status_code == 200:
            files = response.json()
            print(f"\nFound {len(files)} files:")
            for f in files:
                print(f"- {f['file_name']} ({f['file_size']} bytes)")
        else:
            print("Failed to list files")

if __name__ == "__main__":
    # Example usage
    # asyncio.run(upload_file("test.txt"))
    # asyncio.run(list_files())
    print("Edit the script with your API_KEY and file path to test.")
