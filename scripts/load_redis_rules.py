# import redis
# import os

# # Set up
# REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
# REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# # Kết nối Redis
# r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# # Example rules
# blacklist_accounts = ["12345", "67890"]
# country_blacklist = ["NG", "KP"]

# # Load vào Redis
# def load_blacklist():
#     for acc in blacklist_accounts:
#         r.sadd("blacklist_accounts", acc)  # Set Redis
#     for country in country_blacklist:
#         r.sadd("blacklist_countries", country)
#     print("Rules loaded into Redis")

# if __name__ == "__main__":
#     load_blacklist()
