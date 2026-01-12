import { add } from "./index.js";

if (add(2, 3) !== 5) {
  throw new Error("add(2, 3) should be 5");
}

console.log("ok");

