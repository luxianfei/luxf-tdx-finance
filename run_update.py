from fetchers.incremental_updater import IncrementalUpdater

def progress_callback(progress, message):
    print(f'进度: {progress:.1f}% - {message}')

updater = IncrementalUpdater()
result = updater.update_market_snapshot(callback=progress_callback)
print(f'\n更新完成! 成功: {result["success"]}, 失败: {result["failed"]}')
updater.db_client.close()
