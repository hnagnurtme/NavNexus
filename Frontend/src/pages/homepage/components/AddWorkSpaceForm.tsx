
import { WorkSpaceContext } from "@/contexts/WorkSpaceContext";
import { useState,  FormEvent, useContext } from "react";

type WorkspacePayload = {
  name: string;
  description?: string;
  visibility: "private" | "team" | "public";
  color: string;
  documents: File[];
};

type Props = {
  onCreate?: (payload: WorkspacePayload) => Promise<void> | void;
  onCancel?: () => void;
};


export default function AddWorkSpaceForm({ onCreate, onCancel }: Props) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [visibility, setVisibility] =useState<WorkspacePayload["visibility"]>("team");
  const [color, setColor] = useState("#03C75A"); // Naver green default
  const [files] = useState<File[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<{ name?: string } | null>(null);
  const { handleCreateWorkSpace } = useContext(WorkSpaceContext);



  async function submit(e: FormEvent) {
    e.preventDefault();
    setErrors(null);
    if (!name.trim()) {
      setErrors({ name: "Workspace name is required." });
      return;
    }

    const payload: WorkspacePayload = {
      name: name.trim(),
      description: description.trim(),
      visibility,
      color,
      documents: files,
    };

    try {
      setIsSubmitting(true);
      await handleCreateWorkSpace(
        payload.name,
        payload.description || "",
        files.map((f) => f.name)
      );
      console.log(files);
      await onCreate?.(payload);
    } catch (err) {
      console.error("Failed to create workspace", err);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={submit}
      className="max-w-3xl w-full rounded-2xl bg-[#0d0d0d] border border-[#222] p-6 text-[#f5f5f5] shadow-[0_10px_30px_rgba(0,0,0,0.6)]"
    >
      <div className="flex items-start gap-6">
        {/* Left: form inputs */}
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-[#03C75A]">
            Create a new workspace
          </h3>
          <p className="text-sm text-[#b3b3b3] mt-1">
            A workspace keeps documents, notes and insights together.
          </p>

          <div className="mt-6 space-y-4">
            <div>
              <label className="block text-xs font-medium text-[#bfcfc3]">
                Workspace name
              </label>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Ex: Climate Research Group"
                className={`mt-2 w-full rounded-lg border px-3 py-2 bg-[#0b0b0b] placeholder:text-[#777] focus:outline-none focus:ring-2 focus:ring-[#03C75A]/40 ${
                  errors?.name ? "border-red-500" : "border-[#222]"
                }`}
                aria-invalid={!!errors?.name}
                aria-describedby={errors?.name ? "name-error" : undefined}
              />
              {errors?.name && (
                <p id="name-error" className="mt-1 text-xs text-red-400">
                  {errors.name}
                </p>
              )}
            </div>

            <div>
              <label className="block text-xs font-medium text-[#bfcfc3]">
                Description
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                placeholder="Short summary about the workspace"
                className="mt-2 w-full resize-none rounded-lg border px-3 py-2 bg-[#0b0b0b] placeholder:text-[#777] border-[#222] focus:outline-none focus:ring-2 focus:ring-[#03C75A]/40"
              />
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-xs font-medium text-[#bfcfc3]">
                  Visibility
                </label>
                <div className="flex gap-2 mt-2">
                  {(
                    [
                      "private",
                      "team",
                      "public",
                    ] as WorkspacePayload["visibility"][]
                  ).map((v) => (
                    <button
                      key={v}
                      type="button"
                      onClick={() => setVisibility(v)}
                      className={`rounded-full px-3 py-1 text-sm font-medium border ${
                        visibility === v
                          ? "bg-[#03C75A] text-black border-transparent"
                          : "bg-[#111] text-[#cfcfcf] border-[#2a2a2a]"
                      }`}
                      aria-pressed={visibility === v}
                    >
                      {v}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-[#bfcfc3]">
                  Accent color
                </label>
                <div className="flex items-center gap-3 mt-2">
                  <input
                    aria-label="Choose workspace color"
                    value={color}
                    onChange={(e) => setColor(e.target.value)}
                    type="color"
                    className="h-10 w-12 rounded-md border border-[#222] p-0"
                  />

                  <div className="flex gap-2">
                    {/* quick swatches */}
                    {["#03C75A", "#00A84D", "#94b49f", "#2f3b2f"].map((sw) => (
                      <button
                        key={sw}
                        type="button"
                        onClick={() => setColor(sw)}
                        aria-label={`Use ${sw}`}
                        className={`h-8 w-8 rounded-full border ${
                          color === sw
                            ? "ring-2 ring-[#03C75A]/60"
                            : "border-[#222]"
                        }`}
                        style={{ backgroundColor: sw }}
                      />
                    ))}
                  </div>
                </div>
              </div>
            </div>


            <div className="flex items-center gap-3 mt-2">
              <button
                disabled={isSubmitting}
                type="submit"
                className="inline-flex items-center gap-2 rounded-full bg-[#03C75A] px-5 py-2 text-sm font-semibold text-black shadow hover:scale-[1.02] disabled:opacity-60"
              >
                {isSubmitting ? "Creating..." : "Create workspace"}
              </button>

              <button
                type="button"
                onClick={onCancel}
                className="inline-flex items-center gap-2 rounded-full border border-[#2a2a2a] bg-[#111] px-4 py-2 text-sm text-[#cfcfcf]"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>

        {/* Right: preview */}
        <aside className="w-80 shrink-0">
          <div
            className="rounded-xl border border-[#222]  p-4"
            style={{
              background: `linear-gradient(180deg, ${color}22, #0b0b0b)`,
            }}
          >
            <div className="flex items-center gap-3">
              <div
                className="w-12 h-12 rounded-lg"
                style={{ backgroundColor: color }}
              />
              <div>
                <div className="text-sm font-semibold text-[#f5f5f5]">
                  {name || "Workspace name"}
                </div>
                <div className="text-xs text-[#b3b3b3]">
                  {visibility} workspace
                </div>
              </div>
            </div>

            <p className="mt-3 text-xs text-[#cfcfcf] truncate">
              {description || "A short workspace summary will appear here."}
            </p>

            <div className="mt-4 flex items-center gap-2 text-xs text-[#b3b3b3]">
              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[#03C75A]/20 text-[#03C75A] font-semibold">
                {files.length}
              </div>
              <div>{files.length} docs</div>
            </div>

            <div className="mt-4 text-[11px] text-[#9aa69a]">
              Preview updates as you type. Accent color is applied to the card
              and CTA.
            </div>
          </div>
        </aside>
      </div>
    </form>
  );
}
