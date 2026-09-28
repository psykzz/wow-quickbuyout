import unittest
from pathlib import Path

from lupa import LuaRuntime


SOURCE = (Path(__file__).resolve().parents[1] / "QuickBuyout.lua").read_text()

WOW_API = """
Enum = {ItemClass = {Weapon=2, Armor=4, Consumable=0, Gem=3,
    ItemEnhancement=8, CurrencyTokenObsolete=10, PermanentObsolete=14,
    Miscellaneous=15}}
local names = {[2]="Weapons", [4]="Armor", [0]="Consumables",
    [3]="Generic(OBSOLETE)", [8]="Jewelry(OBSOLETE)",
    [10]="Money(OBSOLETE)", [14]="Permanent(OBSOLETE)", [15]="Miscellaneous"}
local items = {[101]=2, [102]=0, [103]=15, [104]=3, [105]=10}
C_Item = {
    GetItemInfoInstant = function(id) return id, "", "", "", "", items[id] end,
    GetItemClassInfo = function(id) return names[id] end,
}
QuickBuyoutDB = {["15"]=true, ["3"]=true, ["10"]=true}
Settings = {VarType={Boolean="boolean"}, settings={}}
function Settings.RegisterVerticalLayoutCategory(name) return name end
function Settings.RegisterAddOnSetting(category, id, key, db, kind, name, default)
    if db[key] == nil then db[key] = default end
    Settings.settings[id] = {key=key, name=name, default=default}
    return Settings.settings[id]
end
function Settings.CreateCheckbox() end
function Settings.RegisterAddOnCategory(category) Settings.category = category end
results = {}
C_AuctionHouse = {
    GetNumItemSearchResults = function() return #results end,
    GetItemSearchResultInfo = function(_, i) return results[i] end,
    PlaceBid = function(id, amount) purchased = {id, amount} end,
}
AuctionHouseUtil = {IsOwnedAuction=function(info) return info.owned end}
C_Timer = {After=function() end}
UIErrorsFrame = {AddExternalErrorMessage=function(_, message) error(message) end}
function GetMoney() return 10000 end
function wipe(t) for key in pairs(t) do t[key] = nil end end
function hooksecurefunc(frame, method, fn) frame.onItemKey = fn end
function CreateFrame()
    events = {RegisterEvent=function() end}
    function events:SetScript(_, fn) self.onEvent = fn end
    return events
end
C_AddOns = {IsAddOnLoaded=function() return true end}
local list = {}
function list:GetSelectedEntry() return self.selected end
function list:SetSelectedEntry(info) self.selected = info end
AuctionHouseFrame = {ItemBuyFrame = {ItemList=list, BuyoutFrame={}}}
local frame = AuctionHouseFrame.ItemBuyFrame
function frame:IsShown() return true end
function frame:HookScript(_, fn) self.onSearchEvent = fn end
function frame:BuyoutItem() self.blizzardBuys = (self.blizzardBuys or 0) + 1 end
function frame.BuyoutFrame:SetBuyoutCallback(fn) self.click = fn end
function frame:GetAuctionHouseFrame() return AuctionHouseFrame end
"""


class QuickBuyoutTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(WOW_API)
        self.lua.execute(SOURCE)
        self.lua.execute("""
            results = {
                {auctionID=10, buyoutAmount=200},
                {auctionID=11, buyoutAmount=100},
            }
        """)

    def test_settings_default_to_gear_and_preserve_saved_categories(self):
        self.lua.execute("""
            assert(Settings.category == "Quick Buyout")
            assert(Settings.settings.QUICKBUYOUT_CLASS_2 and Settings.settings.QUICKBUYOUT_CLASS_4)
            assert(Settings.settings.QUICKBUYOUT_CLASS_0 and Settings.settings.QUICKBUYOUT_CLASS_15)
            assert(not Settings.settings.QUICKBUYOUT_CLASS_3)
            assert(not Settings.settings.QUICKBUYOUT_CLASS_8)
            assert(not Settings.settings.QUICKBUYOUT_CLASS_10)
            assert(not Settings.settings.QUICKBUYOUT_CLASS_14)
            assert(QuickBuyoutDB["2"] and QuickBuyoutDB["4"])
            assert(QuickBuyoutDB["0"] == false and QuickBuyoutDB["15"])
        """)

    def test_only_enabled_classes_use_quick_buyout(self):
        self.lua.execute("""
            local frame = AuctionHouseFrame.ItemBuyFrame
            frame.itemKey = {itemID=101}
            frame.onItemKey()
            assert(frame.ItemList.selected.auctionID == 11)
            frame.ItemList.selected = results[1]
            frame.BuyoutFrame.click()
            assert(purchased[1] == 10 and purchased[2] == 200)
            events.onEvent(events, "AUCTION_HOUSE_PURCHASE_COMPLETED", 10)

            frame.itemKey = {itemID=102}
            frame.ItemList.selected = nil
            frame.onItemKey()
            assert(frame.ItemList.selected == nil)
            frame.BuyoutFrame.click()
            assert(frame.blizzardBuys == 1)

            QuickBuyoutDB["0"] = true
            frame.onSearchEvent(frame, "ITEM_SEARCH_RESULTS_UPDATED")
            assert(frame.ItemList.selected.auctionID == 11)
            frame.BuyoutFrame.click()
            assert(purchased[1] == 11)
            events.onEvent(events, "AUCTION_HOUSE_PURCHASE_COMPLETED", 11)

            QuickBuyoutDB["0"] = false
            frame.BuyoutFrame.click()
            assert(frame.blizzardBuys == 2)
            results = {{auctionID=12, buyoutAmount=50}}
            frame.itemKey = {itemID=103}
            frame.ItemList.selected = nil
            frame.onItemKey()
            assert(frame.ItemList.selected.auctionID == 12)
            QuickBuyoutDB["2"] = false
            frame.itemKey = {itemID=101}
            frame.BuyoutFrame.click()
            assert(frame.blizzardBuys == 3)
            for _, itemID in ipairs({104, 105}) do
                frame.itemKey = {itemID=itemID}
                frame.ItemList.selected = nil
                frame.onItemKey()
                assert(frame.ItemList.selected == nil)
                frame.BuyoutFrame.click()
            end
            assert(frame.blizzardBuys == 5)
        """)


if __name__ == "__main__":
    unittest.main()
