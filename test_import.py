try:
    from api import admin
    print('Admin module imported successfully')
except Exception as e:
    print(f'Import error: {e}')
    import traceback
    traceback.print_exc()