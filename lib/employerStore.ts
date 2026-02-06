// NOTE: Request instance Store per Nextjs Redux starter here: https://redux.js.org/usage/nextjs#folder-structure
import { configureStore } from "@reduxjs/toolkit";
import employerReducer, {
  EmployerState,
} from "./features/profileCreation/employerSlice";
import saveReducer from "./features/profileCreation/saveSlice";

interface PreloadedState {
  employer: EmployerState;
}

// WARNING: preloadedState MUST utilize the interface which MUST match the same slices used for the reducers
// WARNING: The ConfigureStoreOptions MUST be passed directly into configureStore without having its type specified
export const makeStore = (preloadedState?: PreloadedState) =>
  configureStore({
    reducer: {
      employer: employerReducer,
      save: saveReducer,
    },
    preloadedState,
    devTools: process.env.NODE_ENV !== "production",
    // middleware: (getDefaultMiddleware) => getDefaultMiddleware().concat(loggerMiddleware),
  });

// Infer the type of makeStore
export type AppStore = ReturnType<typeof makeStore>;

// Infer the `RootState` and `AppDispatch` types from the store itself
export type RootState = ReturnType<AppStore["getState"]>;
export type AppDispatch = AppStore["dispatch"];
