export function calculatePriceChange(currentPrice: number, previousPrice: number | undefined) {
  if (previousPrice === undefined || previousPrice === 0) {
    return { changeValue: 0, changePercentage: 0 };
  }

  const changeValue = currentPrice - previousPrice;
  const changePercentage = (changeValue / previousPrice) * 100;

  return { changeValue, changePercentage };
}

export function getPriceTrend(changeValue: number) {
  if (changeValue > 0) {
    return 'up';
  } else if (changeValue < 0) {
    return 'down';
  } else {
    return 'same';
  }
}
