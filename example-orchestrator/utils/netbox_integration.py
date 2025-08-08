"""
NetBox Integration APIs for Intent Based Orchestrator UI
Provides data endpoints for enhanced dashboard and NetBox management.
"""
import requests
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from settings import Settings
from fastapi import HTTPException

logger = logging.getLogger(__name__)
settings = Settings()

class NetBoxIntegrationAPI:
    """
    Low-code API wrapper for NetBox integration with comprehensive error handling.
    Provides data for dashboard statistics, import progress, and management operations.
    """
    
    def __init__(self):
        self.netbox_url = getattr(settings, 'NETBOX_URL', 'http://127.17.0.1:8000')
        self.netbox_token = getattr(settings, 'NETBOX_TOKEN', 'faf1b318bf1ae5ff6f5f2158b29392715fe8ebc9')
        self.headers = {
            'Authorization': f'Token {self.netbox_token}',
            'Content-Type': 'application/json'
        }
    
    def get_dashboard_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive dashboard statistics for the main UI page.
        Returns device counts, manufacturer counts, and recent activity.
        """
        try:
            stats = {
                'netbox_status': 'connected',
                'total_manufacturers': 0,
                'total_device_types': 0,
                'total_devices': 0,
                'recent_imports': [],
                'popular_manufacturers': [],
                'last_updated': datetime.now().isoformat()
            }
            
            # Get manufacturer count
            response = requests.get(f'{self.netbox_url}/api/dcim/manufacturers/', headers=self.headers, timeout=10)
            if response.status_code == 200:
                manufacturers_data = response.json()
                stats['total_manufacturers'] = manufacturers_data.get('count', 0)
                
                # Get top manufacturers by device count
                manufacturers = manufacturers_data.get('results', [])[:5]
                stats['popular_manufacturers'] = [
                    {'name': mfg['name'], 'slug': mfg['slug']} 
                    for mfg in manufacturers
                ]
            
            # Get device types count
            response = requests.get(f'{self.netbox_url}/api/dcim/device-types/', headers=self.headers, timeout=10)
            if response.status_code == 200:
                stats['total_device_types'] = response.json().get('count', 0)
            
            # Get devices count
            response = requests.get(f'{self.netbox_url}/api/dcim/devices/', headers=self.headers, timeout=10)
            if response.status_code == 200:
                stats['total_devices'] = response.json().get('count', 0)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get dashboard statistics: {e}")
            return {
                'netbox_status': 'error',
                'error': str(e),
                'total_manufacturers': 0,
                'total_device_types': 0,
                'total_devices': 0,
                'recent_imports': [],
                'popular_manufacturers': [],
                'last_updated': datetime.now().isoformat()
            }
    
    def get_import_status(self) -> Dict[str, Any]:
        """
        Get current import status and progress for real-time updates.
        """
        # This would integrate with your workflow system
        # For now, return mock data structure
        return {
            'active_imports': [],
            'completed_imports': [],
            'failed_imports': [],
            'import_queue_size': 0
        }
    
    def get_manufacturer_summary(self) -> List[Dict[str, Any]]:
        """
        Get detailed manufacturer information for management UI.
        """
        try:
            response = requests.get(f'{self.netbox_url}/api/dcim/manufacturers/', headers=self.headers, timeout=10)
            if response.status_code == 200:
                manufacturers = response.json().get('results', [])
                summary = []
                
                for mfg in manufacturers:
                    # Get device count for each manufacturer
                    device_response = requests.get(
                        f'{self.netbox_url}/api/dcim/device-types/?manufacturer_id={mfg["id"]}',
                        headers=self.headers,
                        timeout=5
                    )
                    device_count = 0
                    if device_response.status_code == 200:
                        device_count = device_response.json().get('count', 0)
                    
                    summary.append({
                        'id': mfg['id'],
                        'name': mfg['name'],
                        'slug': mfg['slug'],
                        'device_count': device_count,
                        'description': mfg.get('description', ''),
                        'url': mfg.get('url', '')
                    })
                
                return sorted(summary, key=lambda x: x['device_count'], reverse=True)
                
        except Exception as e:
            logger.error(f"Failed to get manufacturer summary: {e}")
            return []
    
    def search_devices(self, query: str, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Advanced device search with filtering capabilities.
        """
        try:
            search_params = {'q': query} if query else {}
            if filters:
                search_params.update(filters)
            
            response = requests.get(
                f'{self.netbox_url}/api/dcim/device-types/',
                headers=self.headers,
                params=search_params,
                timeout=10
            )
            
            if response.status_code == 200:
                results = response.json().get('results', [])
                return [
                    {
                        'id': device['id'],
                        'model': device['model'],
                        'manufacturer': device['manufacturer']['name'],
                        'slug': device['slug'],
                        'part_number': device.get('part_number', ''),
                        'u_height': device.get('u_height', 0)
                    }
                    for device in results
                ]
            
        except Exception as e:
            logger.error(f"Failed to search devices: {e}")
            
        return []

# Global instance
netbox_api = NetBoxIntegrationAPI()
