/**
 * PhoenixML Reusable Theme Hook
 * Re-exports useTheme and ThemeProvider from ThemeContext
 */
import { useTheme } from '../context/ThemeContext.jsx';

export {
  useTheme,
  ThemeProvider,
  THEME_STORAGE_KEY,
  VALID_THEMES,
  DEFAULT_THEME,
  validateTheme,
  getInitialTheme,
  applyThemeToDom,
} from '../context/ThemeContext.jsx';

export default useTheme;
