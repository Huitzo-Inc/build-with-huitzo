/// <reference types="vite/client" />

// The SDK ships its design tokens as a CSS side-effect import. Declare it so
// `import '@huitzo/dashboard-sdk-react/styles'` typechecks under strict mode.
declare module "@huitzo/dashboard-sdk-react/styles";
