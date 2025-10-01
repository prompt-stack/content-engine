"""
Example: Creating a Content Enrichment Workflow
Demonstrates current workflow creation patterns.
"""

import requests

class ContentEngineWorkflow:
    def __init__(self, base_url="http://localhost:9765"):
        self.base_url = base_url
    
    def enrich_content(self, url):
        """Complete workflow: Extract → Summarize → Tags → Image"""
        
        # Step 1: Extract (Call 1)
        extract = requests.post(f"{self.base_url}/api/extract/auto", json={"url": url}).json()
        
        # Step 2: Summarize (Call 2)
        summary = requests.post(
            f"{self.base_url}/api/llm/process-content",
            json={"content": extract["content"], "task": "summarize", "provider": "deepseek"}
        ).json()
        
        # Step 3: Tags (Call 3)
        tags = requests.post(
            f"{self.base_url}/api/llm/process-content",
            json={"content": extract["content"], "task": "generate_tags", "provider": "openai"}
        ).json()
        
        # Step 4: Image (Call 4)
        image = requests.post(
            f"{self.base_url}/api/media/generate-from-content",
            json={"content": summary["result"], "provider": "openai"}
        ).json()
        
        return {
            "title": extract["title"],
            "summary": summary["result"],
            "tags": tags["result"],
            "image_url": image["image_url"]
        }

# Usage
workflow = ContentEngineWorkflow()
result = workflow.enrich_content("https://www.tiktok.com/@hoffdigital/video/7535517761863224606")
print(result)
