"use client";

import { useEffect, useState } from "react";
import { ApiError, apiRequest } from "@/lib/api/client";
import { Plus, Trash2, Image as ImageIcon } from "lucide-react";

type PhotoItem = {
  id: number;
  image: string;
  title: string;
  caption: string;
  display_order: number;
  is_active: boolean;
  created_at: string;
};

export function GalleryTab() {
  const [photos, setPhotos] = useState<PhotoItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [title, setTitle] = useState("");
  const [caption, setCaption] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");

  async function fetchPhotos() {
    try {
      const res = await apiRequest<any>({ path: "/mosques/my-mosque/photos/" });
      const items = Array.isArray(res) ? res : res.results || [];
      setPhotos(items);
    } catch (err) {
      console.error("Failed to load mosque photos", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchPhotos();
  }, []);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setError("Please select an image file to upload.");
      return;
    }

    setUploading(true);
    setSuccess("");
    setError("");

    const formData = new FormData();
    formData.append("image", selectedFile);
    if (title) formData.append("title", title);
    if (caption) formData.append("caption", caption);

    try {
      await apiRequest({
        path: "/mosques/my-mosque/photos/",
        method: "POST",
        body: formData,
      });
      setSuccess("Mosque photo uploaded successfully!");
      setTitle("");
      setCaption("");
      setSelectedFile(null);
      fetchPhotos();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message || "Failed to upload photo.");
      } else {
        setError("An unexpected error occurred.");
      }
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this photo from the mosque gallery?")) return;
    try {
      await apiRequest({
        path: `/mosques/my-mosque/photos/${id}/`,
        method: "DELETE",
      });
      setSuccess("Photo removed.");
      fetchPhotos();
    } catch (err) {
      console.error("Failed to delete photo", err);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-slate-500">Loading photo gallery...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Upload Form */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center space-x-2">
          <span>🖼️</span>
          <span>Upload Mosque Photo</span>
        </h2>

        {success && (
          <div className="mb-4 p-4 bg-emerald-50 text-emerald-700 rounded-lg border border-emerald-200 text-sm font-medium">
            {success}
          </div>
        )}

        {error && (
          <div className="mb-4 p-4 bg-rose-50 text-rose-700 rounded-lg border border-rose-200 text-sm font-medium">
            {error}
          </div>
        )}

        <form onSubmit={handleUpload} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Image File *</label>
              <input
                type="file"
                accept="image/*"
                onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Photo Title</label>
              <input
                type="text"
                placeholder="e.g. Main Prayer Hall"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 text-slate-900"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Caption / Description</label>
            <input
              type="text"
              placeholder="e.g. Spacious carpeted prayer hall for daily congregation"
              value={caption}
              onChange={(e) => setCaption(e.target.value)}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 text-slate-900"
            />
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={uploading}
              className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-lg shadow-sm transition disabled:opacity-50 flex items-center space-x-2"
            >
              <Plus className="h-4 w-4" />
              <span>{uploading ? "Uploading..." : "Upload Photo"}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Gallery Grid */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h3 className="text-lg font-bold text-slate-900 mb-4">Mosque Gallery ({photos.length})</h3>

        {photos.length === 0 ? (
          <div className="p-8 text-center text-slate-500 bg-slate-50 rounded-xl border border-dashed border-slate-200">
            <ImageIcon className="h-10 w-10 mx-auto mb-2 text-slate-400" />
            <p className="font-medium">No photos uploaded yet.</p>
            <p className="text-xs text-slate-400 mt-1">Upload photos to showcase your mosque exterior, prayer hall, and facilities.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
            {photos.map((photo) => (
              <div key={photo.id} className="group relative rounded-xl border border-slate-200 overflow-hidden bg-slate-50 shadow-xs">
                <div className="aspect-video w-full overflow-hidden bg-slate-100 relative">
                  <img
                    src={photo.image}
                    alt={photo.title || "Mosque Photo"}
                    className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
                  />
                  <button
                    type="button"
                    onClick={() => handleDelete(photo.id)}
                    className="absolute top-2 right-2 p-2 bg-rose-600/90 hover:bg-rose-700 text-white rounded-full shadow-md transition opacity-90 hover:opacity-100"
                    title="Delete Photo"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
                <div className="p-3">
                  <h4 className="font-semibold text-slate-900 text-sm">{photo.title || "Mosque Photo"}</h4>
                  {photo.caption && <p className="text-xs text-slate-500 mt-0.5">{photo.caption}</p>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
