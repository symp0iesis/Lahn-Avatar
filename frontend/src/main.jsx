import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import "./index.css";

import LahnAvatarChat from "./App.jsx";
import ExperienceUploadPage from "./ExperienceUploadPage.jsx";
import Layout from "./Layout.jsx"; // <-- new layout component with sidebar

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<LahnAvatarChat />} />  {/* 👈 Default route for "/" */}
          <Route path="chat" element={<LahnAvatarChat />} />
          <Route path="experience" element={<ExperienceUploadPage />} />
          <Route path="*" element={<LahnAvatarChat />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>
);
