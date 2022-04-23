fetch("https://kite.zerodha.com/oms/orders/regular", {
  "headers": {
    "accept": "application/json, text/plain, */*",
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
    "accept-language": "en-US,en;q=0.9",
    "authorization": "enctoken IS2gDX0zwGmagNGa3GZ+JYBzp7UxJWE0lhqQgHFQc61QnXSPVCLYYd97hfeWEaRqQtFfU2w7R141WFLdl99tlGk3tpgzmwdbPBDu0roVXfi0s4AqaGHA1w==",
    "cache-control": "no-cache",
    "content-type": "application/x-www-form-urlencoded",
    "pragma": "no-cache",
    "sec-ch-ua": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"98\", \"Google Chrome\";v=\"98\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"macOS\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "x-kite-userid": "XQ9712",
    "x-kite-version": "2.9.10"
  },
  "referrer": "https://kite.zerodha.com/dashboard",
  "referrerPolicy": "strict-origin-when-cross-origin",
  "body": "variety=regular&exchange=NFO&tradingsymbol=NIFTY2230315500PE&transaction_type=BUY&order_type=MARKET&quantity=50&price=0&product=MIS&validity=DAY&disclosed_quantity=0&trigger_price=0&squareoff=0&stoploss=0&trailing_stoploss=0&user_id=XQ9712",
  "method": "POST",
  "mode": "cors",
  "credentials": "include"
});

data={"variety": "regular","exchange":"NFO","tradingsymbol":"NIFTY2230315500PE",transaction_type=BUY&order_type=MARKET&quantity=50&price=0&product=MIS&validity=DAY&disclosed_quantity=0&trigger_price=0&squareoff=0&stoploss=0&trailing_stoploss=0&user_id=XQ9712}


fetch("https://kite.zerodha.com/oms/orders/regular", {
  "headers": {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-US,en;q=0.9",
    "authorization": "enctoken IS2gDX0zwGmagNGa3GZ+JYBzp7UxJWE0lhqQgHFQc61QnXSPVCLYYd97hfeWEaRqQtFfU2w7R141WFLdl99tlGk3tpgzmwdbPBDu0roVXfi0s4AqaGHA1w==",
    "cache-control": "no-cache",
    "content-type": "application/x-www-form-urlencoded",
    "pragma": "no-cache",
    "sec-ch-ua": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"98\", \"Google Chrome\";v=\"98\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"macOS\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "x-kite-userid": "XQ9712",
    "x-kite-version": "2.9.10"
  },
  "referrer": "https://kite.zerodha.com/positions",
  "referrerPolicy": "strict-origin-when-cross-origin",
  "body": "variety=regular&exchange=NFO&tradingsymbol=NIFTY2230315500PE&transaction_type=SELL&order_type=MARKET&quantity=50&price=0&product=MIS&validity=DAY&disclosed_quantity=0&trigger_price=0&squareoff=0&stoploss=0&trailing_stoploss=0&user_id=XQ9712",
  "method": "POST",
  "mode": "cors",
  "credentials": "include"
});