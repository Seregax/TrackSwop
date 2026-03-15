from src.model.services.providers.vk.vk_service import VkService

service = VkService()

service.set_auth_data("vk1.a.OyQHhBT2VlYIKUOcaAQi7APglefMTJLQnHIxWrmls97b0k1-DdmoTI83hzlh_doNWsk3QZUmHLTwaXJbJyc_JiwgJeHTM7bHmllfBTGUhbBvyyClsSNMBWeFLX8cTnD_bTRgdUhz61aKg37IwpC7jep_YMPtBxdGqYb7FYiRxydaa4hMrQBu3qST_hsMQykv5Mqgx1nadr5mR6ZWAsr2kA", 556283071)

service.authenticate()

playlists = service.get_playlists()

print(f"Найдено плейлистов: {len(playlists)}")

for playlist in playlists:
    print(f"- {playlist.name} (ID: {playlist.id}, треков: {playlist.track_count})")

print('done')




