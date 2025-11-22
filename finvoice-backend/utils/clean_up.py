"""
Automatic cleanup of cached audio files
Deletes files older than 24 hours
"""

import os
from pathlib import Path
from datetime import datetime, timedelta
import asyncio
import time

# Audio cache directory
AUDIO_CACHE_DIR = Path("cache/audio")

def cleanup_old_audio_files(hours: int = 24):
    """
    Delete audio files older than specified hours
    
    Args:
        hours: Delete files older than this many hours (default: 24)
        
    Returns:
        dict: Cleanup statistics
    """
    try:
        if not AUDIO_CACHE_DIR.exists():
            print(f"⚠️ Audio cache directory not found: {AUDIO_CACHE_DIR}")
            return {"deleted": 0, "remaining": 0, "error": "Directory not found"}
        
        now = datetime.now()
        cutoff_time = now - timedelta(hours=hours)
        
        deleted_count = 0
        deleted_size = 0
        remaining_count = 0
        
        # Get all audio files
        audio_files = list(AUDIO_CACHE_DIR.glob("*.mp3"))
        
        print(f"\n🗑️ Starting cleanup (deleting files older than {hours}h)...")
        print(f"📁 Directory: {AUDIO_CACHE_DIR}")
        print(f"📊 Total files: {len(audio_files)}")
        
        for audio_file in audio_files:
            # Get file modification time
            file_mtime = datetime.fromtimestamp(audio_file.stat().st_mtime)
            file_age_hours = (now - file_mtime).total_seconds() / 3600
            
            if file_mtime < cutoff_time:
                # File is older than cutoff - delete it
                file_size = audio_file.stat().st_size
                audio_file.unlink()
                
                deleted_count += 1
                deleted_size += file_size
                
                print(f"   ✅ Deleted: {audio_file.name} (age: {file_age_hours:.1f}h)")
            else:
                remaining_count += 1
        
        # Convert size to readable format
        deleted_size_mb = deleted_size / (1024 * 1024)
        
        print(f"\n✅ Cleanup complete!")
        print(f"   🗑️ Deleted: {deleted_count} files ({deleted_size_mb:.2f} MB)")
        print(f"   📂 Remaining: {remaining_count} files")
        
        return {
            "success": True,
            "deleted": deleted_count,
            "deleted_size_mb": round(deleted_size_mb, 2),
            "remaining": remaining_count,
            "cutoff_hours": hours
        }
        
    except Exception as e:
        print(f"❌ Cleanup error: {e}")
        return {
            "success": False,
            "error": str(e),
            "deleted": 0,
            "remaining": 0
        }


async def cleanup_loop(interval_hours: int = 24):
    """
    Run cleanup task in background every X hours
    
    Args:
        interval_hours: Run cleanup every X hours (default: 24)
    """
    print(f"\n🔄 Cleanup task started (runs every {interval_hours}h)")
    
    while True:
        try:
            # Run cleanup
            result = cleanup_old_audio_files(hours=24)
            
            if result.get("success"):
                print(f"✅ Next cleanup in {interval_hours}h")
            
            # Wait for next run
            await asyncio.sleep(interval_hours * 3600)
            
        except Exception as e:
            print(f"❌ Cleanup loop error: {e}")
            await asyncio.sleep(3600)  # Retry in 1 hour on error


def get_cache_stats():
    """
    Get statistics about cached audio files
    
    Returns:
        dict: Cache statistics
    """
    try:
        if not AUDIO_CACHE_DIR.exists():
            return {"error": "Directory not found"}
        
        audio_files = list(AUDIO_CACHE_DIR.glob("*.mp3"))
        
        total_size = sum(f.stat().st_size for f in audio_files)
        total_size_mb = total_size / (1024 * 1024)
        
        # Find oldest and newest files
        if audio_files:
            oldest_file = min(audio_files, key=lambda f: f.stat().st_mtime)
            newest_file = max(audio_files, key=lambda f: f.stat().st_mtime)
            
            oldest_age = (datetime.now() - datetime.fromtimestamp(oldest_file.stat().st_mtime)).total_seconds() / 3600
            newest_age = (datetime.now() - datetime.fromtimestamp(newest_file.stat().st_mtime)).total_seconds() / 3600
        else:
            oldest_age = 0
            newest_age = 0
        
        return {
            "total_files": len(audio_files),
            "total_size_mb": round(total_size_mb, 2),
            "oldest_file_age_hours": round(oldest_age, 1),
            "newest_file_age_hours": round(newest_age, 1)
        }
        
    except Exception as e:
        return {"error": str(e)}


# Manual cleanup function (can be called directly)
def cleanup_now():
    """Run cleanup immediately"""
    return cleanup_old_audio_files(hours=24)


if __name__ == "__main__":
    # Test cleanup
    print("🧪 Testing cleanup system...\n")
    result = cleanup_old_audio_files(hours=24)
    print(f"\n📊 Result: {result}")
    
    print("\n📈 Cache Stats:")
    stats = get_cache_stats()
    print(f"   Files: {stats.get('total_files', 0)}")
    print(f"   Size: {stats.get('total_size_mb', 0)} MB")