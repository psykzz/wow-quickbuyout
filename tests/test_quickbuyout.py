import unittest
from pathlib import Path

from lupa import LuaRuntime


SOURCE = (Path(__file__).resolve().parents[1] / "QuickBuyout.lua").read_text()

WOW_API = """
Enum = {ItemClass = {Weapon=2, Armor=4, Consumable=0, Gem=3,
    ItemEnhancement=8, CurrencyTokenObsolete=10, PermanentObsolete=14,
    Miscellaneous=15, Tradegoods=7}}
local names = {[2]="Weapons", [4]="Armor", [0]="Consumables",
    [3]="Generic(OBSOLETE)", [8]="Jewelry(OBSOLETE)",
    [10]="Money(OBSOLETE)", [14]="Permanent(OBSOLETE)", [15]="Miscellaneous",
    [7]="Trade Goods"}
local items = {[101]=2, [102]=0, [103]=15, [104]=3, [105]=10, [2589]=7}
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
    StartCommoditiesPurchase = function(id, quantity)
        assert(hardwareEvent, "Quote must start from a hardware event")
        quoteRequests = (quoteRequests or 0) + 1
        quoted = {id, quantity}
    end,
    ConfirmCommoditiesPurchase = function(id, quantity)
        commodityBuys = (commodityBuys or 0) + 1
        commodityPurchased = {id, quantity}
    end,
    CancelCommoditiesPurchase = function() cancellations = (cancellations or 0) + 1 end,
    GetQuoteDurationRemaining = function() return quoteDuration or 30 end,
    MakeItemKey = function(id) return {itemID=id} end,
}
AuctionHouseUtil = {IsOwnedAuction=function(info) return info.owned end}
timers = {}
C_Timer = {After=function(_, fn) timers[#timers+1] = fn end}
errors = {}
UIErrorsFrame = {AddExternalErrorMessage=function(_, message) errors[#errors+1] = message end}
AUCTION_HOUSE_TOOLTIP_TITLE_NOT_ENOUGH_MONEY = "Not enough money"
AUCTION_HOUSE_TOOLTIP_TITLE_NONE_AVAILABLE = "None available"
AUCTION_HOUSE_DIALOG_PRICE_UNAVAILABLE = "Price unavailable"
function GetMoney() return money or 10000 end
SOUNDKIT = {IG_MAINMENU_OPTION_CHECKBOX_ON=1}
function PlaySound() end
function wipe(t) for key in pairs(t) do t[key] = nil end end
function hooksecurefunc(frame, method, fn)
    local original = frame[method]
    frame[method] = function(self, ...)
        if original then original(self, ...) end
        fn(self, ...)
    end
    if method == "SetItemKey" then frame.onItemKey = function() fn(frame) end end
end
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
AuctionHouseSearchContext = {BuyCommodities=1}
function AuctionHouseFrame:RefreshSearchResults(context, key)
    refreshed = {context, key.itemID}
end
local display = {itemID=2589, quantity=20, totalPrice=200, shown=true, scripts={}}
AuctionHouseFrame.CommoditiesBuyFrame = {BuyDisplay=display}
function display:GetItemID() return self.itemID end
function display:GetQuantitySelected() return self.quantity end
function display:IsShown() return self.shown end
function display:SetQuantitySelected(quantity) self.quantity = quantity end
function display:SetItemIDAndPrice(id) self.itemID = id end
function display:HookScript(event, fn) self.scripts[event] = fn end
function display:GetAuctionHouseFrame() return AuctionHouseFrame end
display.TotalPrice = {GetAmount=function() return display.totalPrice end}
display.BuyButton = {scripts={}}
function display.BuyButton:GetScript(event) return self.scripts[event] end
function display.BuyButton:SetScript(event, fn) self.scripts[event] = fn end
display.BuyButton:SetScript("OnClick", function()
    if not display.itemID then return end
    blizzardCommodityBuys = (blizzardCommodityBuys or 0) + 1
    C_AuctionHouse.StartCommoditiesPurchase(display.itemID, display.quantity)
end)
function ClickCommodity()
    hardwareEvent = true
    display.BuyButton:GetScript("OnClick")(display.BuyButton)
    hardwareEvent = false
end
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

    def test_linen_cloth_buys_selected_quantity_after_server_quote(self):
        self.lua.execute("""
            QuickBuyoutDB["7"] = true
            ClickCommodity()
            assert(quoted[1] == 2589 and quoted[2] == 20)
            assert(not commodityPurchased)
            events.onEvent(events, "COMMODITY_PRICE_UPDATED", 10, 200)
            assert(commodityPurchased and commodityPurchased[1] == 2589
                and commodityPurchased[2] == 20, "Linen cloth was not purchased")
            assert(not blizzardCommodityBuys, "Confirmation dialog was not bypassed")
        """)

    def test_commodity_classes_remain_opt_in(self):
        self.lua.execute("""
            assert(QuickBuyoutDB["7"] == false)
            ClickCommodity()
            assert(blizzardCommodityBuys == 1 and quoted[2] == 20)
            events.onEvent(events, "COMMODITY_PRICE_UPDATED", 10, 200)
            assert(not commodityPurchased)
        """)

    def test_cheaper_commodity_quote_is_accepted(self):
        self.lua.execute("""
            QuickBuyoutDB["7"] = true
            ClickCommodity()
            events.onEvent(events, "COMMODITY_PRICE_UPDATED", 9, 180)
            assert(commodityPurchased[2] == 20)
        """)

    def test_price_increase_cancels_and_refreshes(self):
        self.lua.execute("""
            QuickBuyoutDB["7"] = true
            ClickCommodity()
            events.onEvent(events, "COMMODITY_PRICE_UPDATED", 11, 201)
            assert(not commodityPurchased and cancellations == 1)
            assert(refreshed[2] == 2589 and #errors == 1)
            events.onEvent(events, "COMMODITY_PRICE_UPDATED", 10, 200)
            assert(not commodityPurchased)
            ClickCommodity()
            assert(quoteRequests == 2)
        """)

    def test_insufficient_money_before_and_after_quote(self):
        self.lua.execute("""
            QuickBuyoutDB["7"] = true
            money = 199
            ClickCommodity()
            assert(not quoted and errors[1] == AUCTION_HOUSE_TOOLTIP_TITLE_NOT_ENOUGH_MONEY)
            money = 200
            ClickCommodity()
            money = 199
            events.onEvent(events, "COMMODITY_PRICE_UPDATED", 10, 200)
            assert(not commodityPurchased and cancellations == 1)
            assert(errors[2] == AUCTION_HOUSE_TOOLTIP_TITLE_NOT_ENOUGH_MONEY)
        """)

    def test_empty_commodity_selection_is_rejected(self):
        for change in ("display.quantity = 0", "display.totalPrice = 0", "display.itemID = nil"):
            with self.subTest(change=change):
                self.setUp()
                self.lua.execute("""
                    QuickBuyoutDB["7"] = true
                    local display = AuctionHouseFrame.CommoditiesBuyFrame.BuyDisplay
                """ + change + """
                    ClickCommodity()
                    assert(not commodityPurchased and not quoteRequests)
                """)

    def test_double_clicks_and_duplicate_quotes_do_not_double_buy(self):
        self.lua.execute("""
            QuickBuyoutDB["7"] = true
            ClickCommodity()
            ClickCommodity()
            assert(quoteRequests == 1)
            events.onEvent(events, "COMMODITY_PRICE_UPDATED", 10, 200)
            ClickCommodity()
            events.onEvent(events, "COMMODITY_PRICE_UPDATED", 10, 200)
            assert(commodityBuys == 1 and quoteRequests == 1)
            events.onEvent(events, "COMMODITY_PURCHASE_SUCCEEDED")
            assert(refreshed[2] == 2589)
            ClickCommodity()
            assert(quoteRequests == 2)
            timers[1]()
            assert(#errors == 0)
            events.onEvent(events, "COMMODITY_PRICE_UPDATED", 10, 200)
            assert(commodityBuys == 2)
        """)

    def test_changed_selection_cancels_pending_quote(self):
        for change in (
            "display:SetQuantitySelected(5)",
            "display:SetItemIDAndPrice(101)",
            'display.shown = false; display.scripts.OnHide()',
            'events.onEvent(events, "AUCTION_HOUSE_CLOSED")',
            'QuickBuyoutDB["7"] = false',
        ):
            with self.subTest(change=change):
                self.setUp()
                self.lua.execute("""
                    QuickBuyoutDB["7"] = true
                    ClickCommodity()
                    local display = AuctionHouseFrame.CommoditiesBuyFrame.BuyDisplay
                """ + change + """
                    events.onEvent(events, "COMMODITY_PRICE_UPDATED", 10, 200)
                    assert(not commodityPurchased and cancellations == 1)
                    timers[1]()
                    assert(#errors == 0)
                """)

    def test_blizzard_quantity_reset_does_not_release_in_flight_guard(self):
        self.lua.execute("""
            QuickBuyoutDB["7"] = true
            ClickCommodity()
            events.onEvent(events, "COMMODITY_PRICE_UPDATED", 10, 200)
            AuctionHouseFrame.CommoditiesBuyFrame.BuyDisplay:SetQuantitySelected(1)
            ClickCommodity()
            assert(quoteRequests == 1)
            events.onEvent(events, "COMMODITY_PURCHASE_SUCCEEDED")
            assert(refreshed[2] == 2589)
        """)

    def test_failed_quote_or_purchase_can_be_retried(self):
        for event in ("COMMODITY_PRICE_UNAVAILABLE", "COMMODITY_PURCHASE_FAILED", "AUCTION_HOUSE_SHOW_ERROR"):
            with self.subTest(event=event):
                self.setUp()
                self.lua.execute("""
                    QuickBuyoutDB["7"] = true
                    ClickCommodity()
                """)
                self.lua.globals().events.onEvent(self.lua.globals().events, event)
                self.lua.execute("""
                    assert(cancellations == 1 and not commodityPurchased)
                    ClickCommodity()
                    assert(quoteRequests == 2)
                    events.onEvent(events, "COMMODITY_PRICE_UPDATED", 10, 200)
                    assert(commodityBuys == 1)
                """)

    def test_timeout_and_expired_quote_do_not_purchase(self):
        for failure in (
            "timers[1]()",
            'quoteDuration = 0; events.onEvent(events, "COMMODITY_PRICE_UPDATED", 10, 200)',
            'events.onEvent(events, "COMMODITY_PRICE_UPDATED", 0, 0)',
        ):
            with self.subTest(failure=failure):
                self.setUp()
                self.lua.execute("""
                    QuickBuyoutDB["7"] = true
                    ClickCommodity()
                """ + failure + """
                    assert(not commodityPurchased and cancellations == 1 and #errors == 1)
                    ClickCommodity()
                    assert(quoteRequests == 2)
                """)

    def test_item_and_commodity_purchases_share_in_flight_guard(self):
        self.lua.execute("""
            QuickBuyoutDB["7"] = true
            local frame = AuctionHouseFrame.ItemBuyFrame
            frame.itemKey = {itemID=101}
            frame.onItemKey()
            ClickCommodity()
            frame.BuyoutFrame.click()
            assert(not purchased)
            events.onEvent(events, "COMMODITY_PRICE_UPDATED", 10, 200)
            events.onEvent(events, "COMMODITY_PURCHASE_SUCCEEDED")
            frame.BuyoutFrame.click()
            assert(purchased[1] == 11)
            ClickCommodity()
            assert(quoteRequests == 1)
            events.onEvent(events, "AUCTION_HOUSE_PURCHASE_COMPLETED", 11)
            ClickCommodity()
            assert(quoteRequests == 2)
        """)

    def test_search_updates_keep_manual_selection_and_skip_unbuyable_auctions(self):
        self.lua.execute("""
            local frame = AuctionHouseFrame.ItemBuyFrame
            frame.itemKey = {itemID=101}
            results = {
                {auctionID=10, buyoutAmount=200},
                {auctionID=11, buyoutAmount=100},
                {auctionID=12, buyoutAmount=1, owned=true},
                {auctionID=13, buyoutAmount=0},
            }
            frame.onItemKey()
            assert(frame.ItemList.selected.auctionID == 11)
            frame.ItemList.selected = results[1]
            frame.onSearchEvent(frame, "ITEM_SEARCH_RESULTS_UPDATED")
            assert(frame.ItemList.selected.auctionID == 10)
            frame.BuyoutFrame.click()
            assert(purchased[1] == 10)
            events.onEvent(events, "AUCTION_HOUSE_PURCHASE_COMPLETED", 10)
            assert(frame.ItemList.selected.auctionID == 11)
            frame.onSearchEvent(frame, "ITEM_SEARCH_RESULTS_UPDATED")
            frame.BuyoutFrame.click()
            assert(purchased[1] == 11)
            events.onEvent(events, "AUCTION_HOUSE_PURCHASE_COMPLETED", 11)
            assert(frame.ItemList.selected == nil)
        """)

    def test_switching_views_after_confirmation_keeps_purchase_guard(self):
        self.lua.execute("""
            QuickBuyoutDB["7"] = true
            ClickCommodity()
            events.onEvent(events, "COMMODITY_PRICE_UPDATED", 10, 200)
            local display = AuctionHouseFrame.CommoditiesBuyFrame.BuyDisplay
            display.shown = false
            display.scripts.OnHide()
            display:SetItemIDAndPrice(101)
            display.shown = true
            ClickCommodity()
            assert(quoteRequests == 1 and not cancellations)
            events.onEvent(events, "COMMODITY_PURCHASE_SUCCEEDED")
            assert(not refreshed, "Do not refresh the previous item into a different view")
            ClickCommodity()
            assert(quoteRequests == 2 and quoted[1] == 101)
        """)


if __name__ == "__main__":
    unittest.main()
