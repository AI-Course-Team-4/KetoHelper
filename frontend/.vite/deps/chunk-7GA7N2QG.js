import {
  require_jsx_runtime
} from "./chunk-SFMRM745.js";
import {
  require_react
} from "./chunk-VKIUPR73.js";
import {
  __toESM
} from "./chunk-QY3AG7D4.js";

// node_modules/@radix-ui/react-direction/dist/index.mjs
var React = __toESM(require_react(), 1);
var import_jsx_runtime = __toESM(require_jsx_runtime(), 1);
var DirectionContext = React.createContext(void 0);
function useDirection(localDir) {
  const globalDir = React.useContext(DirectionContext);
  return localDir || globalDir || "ltr";
}

export {
  useDirection
};
//# sourceMappingURL=chunk-7GA7N2QG.js.map
