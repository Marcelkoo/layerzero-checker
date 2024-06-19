import aiohttp
import asyncio
import pandas as pd
import random

use_proxy = True  # True / False

def get_proxy_dict(proxy):
    if proxy:
        proxy_parts = proxy.split(':')
        return {
            'http': f'http://{proxy_parts[2]}:{proxy_parts[3]}@{proxy_parts[0]}:{proxy_parts[1]}',
            'https': f'http://{proxy_parts[2]}:{proxy_parts[3]}@{proxy_parts[0]}:{proxy_parts[1]}'
        }
    return None

async def fetch_wallet_data(session, wallet, proxies):
    url = f"https://www.layerzero.foundation/api/allocation/{wallet}"
    while True:
        proxy = random.choice(proxies) if proxies else None
        proxy_dict = get_proxy_dict(proxy)
        try:
            async with session.get(url, proxy=proxy_dict['http'] if proxy_dict else None) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            if proxies:
                print(f"Error with proxy {proxy}: {e}")
                proxies.remove(proxy)
                if not proxies:
                    raise RuntimeError("No more proxies available")
            else:
                raise e

async def main():
    with open('wallets.txt') as f:
        wallets = [line.strip() for line in f]

    proxies = None
    if use_proxy:
        with open('proxy.txt') as f:
            proxies = [line.strip() for line in f]
        if not proxies:
            raise RuntimeError("Proxy list is empty")

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_wallet_data(session, wallet, proxies.copy() if proxies else None) for wallet in wallets]
        results = await asyncio.gather(*tasks)

    data = []
    total_zro_allocation = 0
    eligible_count = 0

    for result in results:
        zro_allocation = float(result['zroAllocation']['asString'])
        if zro_allocation > 0:
            eligible_count += 1
            total_zro_allocation += zro_allocation
        wallet_info = {
            "address": result['address'],
            "ZRO Allocation": result['zroAllocation']['asString']
        }
        data.append(wallet_info)

    df = pd.DataFrame(data)
    print(df)
    print(f"Total ZRO Allocation: {total_zro_allocation}")
    print(f"Eligible addresses: {eligible_count}/{len(wallets)}")

    df.to_csv('allocation.csv', index=False)

if __name__ == '__main__':
    asyncio.run(main())
