import { useState } from "react";

export function Counter() {
  const [count, setCount] = useState(0);

  function incrementTwice() {
    setCount(count + 1);
    setCount(count + 1);
  }

  return <button onClick={incrementTwice}>Count: {count}</button>;
}
