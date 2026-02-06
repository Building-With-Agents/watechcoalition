import { createSlice, PayloadAction } from "@reduxjs/toolkit";

export interface SaveState {
  savedPages: {
    [key: string]: boolean;
  };
  isSaved: boolean;
}

const initialState: SaveState = {
  savedPages: {},
  isSaved: true,
};

const saveSlice = createSlice({
  name: "save",
  initialState,
  reducers: {
    setPageDirty: (state, action: PayloadAction<string>) => {
      state.savedPages[action.payload] = false;
      state.isSaved = false;
    },
    setPageSaved: (state, action: PayloadAction<string>) => {
      state.savedPages[action.payload] = true;
      state.isSaved = Object.values(state.savedPages).some((value) => value);
    },
    resetTracking: (state) => {
      Object.keys(state.savedPages).forEach((key) => {
        state.savedPages[key] = true;
      });
      state.isSaved = true;
    },
  },
});

export const { setPageDirty, setPageSaved, resetTracking } = saveSlice.actions;
export default saveSlice.reducer;
