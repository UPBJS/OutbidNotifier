import requests
import json
import os
from colorama import Fore
import time
from plyer import notification
import datetime
from mojang import API

########### COLORS START - IGNORE ###########


def printblue(text, endarg="\n", reset=True):
    if reset:
        print(f"{Fore.BLUE}{text}{Fore.RESET}", end=endarg)
    else:
        print(f"{Fore.BLUE}{text}", end=endarg)


def printred(text, endarg="\n", reset=True):
    if reset:
        print(f"{Fore.RED}{text}{Fore.RESET}", end=endarg)
    else:
        print(f"{Fore.RED}{text}", end=endarg)


def printgreen(text, endarg="\n", reset=True):
    if reset:
        print(f"{Fore.GREEN}{text}{Fore.RESET}", end=endarg)
    else:
        print(f"{Fore.GREEN}{text}", end=endarg)


def printyellow(text, endarg="\n", reset=True):
    if reset:
        print(f"{Fore.YELLOW}{text}{Fore.RESET}", end=endarg)
    else:
        print(f"{Fore.YELLOW}{text}", end=endarg)


def blue(text, reset=True):
    if reset:
        return (f"{Fore.BLUE}{text}{Fore.RESET}")
    else:
        return (f"{Fore.BLUE}{text}")


def yellow(text, reset=True):
    if reset:
        return (f"{Fore.YELLOW}{text}{Fore.RESET}")
    else:
        return (f"{Fore.YELLOW}{text}")


########### COLORS END - IGNORE ###########



def main():
    # API KEY VALIDATION
    os.chdir(os.path.join(__file__, ".."))
    mojangApi = API()

    apikey = open("apiKey.txt", "r").read()

    # NOTE: "test" is not a valid endpoint but it will get mad at you if the api key is invalid regardless
    url = "https://api.hypixel.net/v2/test?key="+apikey
    response = requests.get(url)
    if json.loads(response.content)["cause"] == "Invalid API key":
        printred(
            "[ ERROR ]: [!] Provided API key is not valid, please put a valid Hypixel API key in an apiKey.txt file in the same directory as the script\n           [!] Exiting due to fatal error...")
        exit()
    else:
        printgreen("[+] Validated API key")

    # USERNAME VALIDATION

    validUsername = False

    while not validUsername:
        username = input(
            blue(f"[?] Input your username: {yellow('', reset=False)}", reset=False))

        url = f"https://api.mojang.com/users/profiles/minecraft/{username}"
        response = requests.get(url)
        responseJson = json.loads(response.content)
        try:
            # This should raise a KeyError exception if it doesen't exist so the following code will NOT be executed if the username is valid
            errorMessage = responseJson['errorMessage']
            printred(f"[ ERROR ]: {errorMessage}")
        except KeyError:
            validUsername = True
            printgreen("[+] Validated username")
            playerUUID = responseJson['id']
            pass  # dont do nothing else and continue with the below code because me like spaghetti code

    # IDK WHAT TO NAME THIS SECTION BUT IT ISN'T USERNAME VALIDATION ANYMORE
    alreadyNotifiedAuctionIDs = []
    auctionsWherePlayerIsBidder = []
    printyellow("---- Outbid Notifier is running ----")
    while True:
        url = f"https://api.hypixel.net/v2/skyblock/auctions?key={apikey}"
        response = requests.get(url)
        auctions = response.json()["auctions"]
        # CHECK FOR ANY NEW AUCTIONS
        for auction in auctions:
            for bid in auction["bids"]:
                if bid["bidder"] == playerUUID:  # if the player has bid on an item
                    auctionswpibuuids = [auctionWherePlayerIsBidder["uuid"]
                                         for auctionWherePlayerIsBidder in auctionsWherePlayerIsBidder]
                    if auction["uuid"] in auctionswpibuuids:
                        for auctionWherePlayerIsBidder in auctionsWherePlayerIsBidder:
                            if auction["uuid"] == auctionWherePlayerIsBidder["uuid"]:
                                auctionsWherePlayerIsBidder.remove(
                                    auctionWherePlayerIsBidder)
                                auctionsWherePlayerIsBidder.append(auction)
                    else:
                        auctionsWherePlayerIsBidder.append(auction)

        # REMOVE AUCTIONS THAT EXPIRED
        for auctionWherePlayerIsBidder in auctionsWherePlayerIsBidder:

            if auctionWherePlayerIsBidder["end"] <= int(datetime.datetime.utcnow().timestamp()):
                auctionsWherePlayerIsBidder.remove(auctionWherePlayerIsBidder)
            else:
                continue

        
        for auction in auctionsWherePlayerIsBidder:
            highestBidAmount = auction["highest_bid_amount"]
            bids = auction["bids"]
            for bid in bids:
                if bid["amount"] == highestBidAmount:
                    highestBidderUUID = bid["bidder"]
                    break

            if highestBidderUUID == playerUUID:
                continue
            else:
                if bid["timestamp"] not in alreadyNotifiedAuctionIDs:
                    outbidderUsername = mojangApi.get_username(
                        highestBidderUUID)
                    notification.notify(
                        title=f'Outbid on {auction["item_name"]} by {outbidderUsername}',
                        message=f'You have been outbid by {outbidderUsername} on {auction["item_name"]}, the highest bid is now {highestBidAmount}',
                        timeout=0
                    )
                    alreadyNotifiedAuctionIDs.append(bid["timestamp"])

        time.sleep(5)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        printred("[ ERROR ]: CTRL+C detected, exiting...")
    except requests.exceptions.ConnectionError:
        printred("[ ERROR ]: Connection error, exiting...")
    except Exception as e:
        printred(f"[ UNEXPECTED ERROR ]: {e}")
