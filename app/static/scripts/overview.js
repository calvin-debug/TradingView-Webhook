"use strict";

const cancelBtns = document.querySelectorAll(".delete-ticker");

cancelBtns.forEach((btn) =>
  btn.addEventListener("click", () => {
    cancelBtns.forEach((btn) => {
      btn.style.backgroundImage = 'url("/static/icons/cancel_trade_gray.png")';
      btn.style.pointerEvents = "none";
    });
  })
);
