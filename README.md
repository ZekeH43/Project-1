# Project-1
 Risk and Reward

You have been hired as a financial analyst for an investment firm. Today, your boss stopped by your desk and asked for you and your colleagues help.

She explained that a client, that is has shown interest in the tech and pharmacutical sectors of the market, would like to talk about investment opportunities and create trading portfolios centered around the short and long term. She mentioned this would be a good opportunity to use a MC Simulation to visualize the potential risk and reward of our chosen stocks.

Your job is to build visualizations and MC Simulations to predict the potental losses and gains of varying Pharmacutical and tech stocks(6 high and low volatility of each sector) and create a short term and long term portfolio that maximizes our clients gains while minimizing their losses. The client has 15,000 dollars (based on a $100,000 yearly salary) to invest in these portfolios

## Instructions

Using the starter code complete the following steps.

First set up the steps for a Monte Carlo simulation for an individual stock, in this case we used NVDA

1. Import the necessary libraries and dependencies.

2. Create a `.env` file in the same directory as your starter code.

3. Inside the `.env` file, include a variable for `ALPACA_API_KEY` and `ALPACA_SECRET_KEY` to access the Alpaca API.

4. Setup the Alpaca API environment

5. Using yfinance, query the database and get 5 year's worth of daily stock information for the following stock:

    * `NVDA - Nvidia Corp

6. Retrieve daily data of stock information

7. Reset the index and remove Adjusted Close column then reprint the remaining columns

8. Find the closing stock price for each ticker and, using the stock budget of $2500 and the last quote, find the current value and amount of the ticker


9. Set your `timeframe`, `start` and `end` dates, and your `ticker` information!
10. Set up a MC Simulation using 500 simulations, 252 trading days and 1 year
11. Optional: use warnings.filterwarnings("ignore") to filter out the warning messages from running the MC Simulation
12. Calculate cumulative return to run the MC Simulation
13. Run a plot of the simulation
14.  Set initial investment
Use the lower and upper `95%` confidence intervals to calculate the range of the possible outcomes of our $2500
Print results
15. Define a function using the code for NVDA stock earlier 
16. Use this function to run MC Simulations for the following tickers for 1,3,5,8,10,and 15 year intervals

    * ARCT - Arcturus Therapeutics Holdings Inc
    * INMD - Inmode Ltd
    * MRK - Merck & Co Inc
    * BMY - Bristol-Myers Squibb Co
    * PFE - Pfizer Inc.
    * SCYX - SCYNEXIS Inc
    * AOSL - Alpha and Omega Semiconductor Ltd
    * DELL - Dell Technologies Inc
    * EBIX - Ebix Inc
    * NTES - NetEase Inc
    * NVDA - Nvidia Corps
    * VZ - Verizon Communications Inc.

17. Create a table of the highs, lows and averages for each MC Simulation for each ticker
18. Create a short term trading portfolio and a long tern trading portfolio based on the information given in the MC Simulations
19. Summarize viabilty of a short term and long term investing strategy using the MC Simulation data found.

#####Results:

Portolio 1 Short Term:
    * EBIX, VZ, ARCT, INMD, PFE

Portfolio 2 Long Term: 
    * NVDA, AOSL, NTES, DELL, MRK

    Not included:
    SCYX

    We determined, with the data given with the MC Simulations, that placing these stocks in their respective portfolios would have the greatest potential benefit while curbing potential loss. We did not include SCYX in any portfolio due to a stock split occurring in 2020 that tainted the MC Simulation. It is also important to remember that MC Simulations should not be relied on completely to make investing decisions but should instead be used to analyze the potential risk of a stock to gain a clearer picture. A MC Simulation can predict a variety of outcomes, but it often cannot predict the unpredictable and the further out you simulate the more unpredictable it gets.
