import { Chat } from "@/components/chat";

export default function Home() {
  return (
    <div className="flex flex-1 flex-col bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <header className="border-b border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
        <div className="mx-auto flex w-full max-w-3xl items-center justify-between gap-4 px-4 py-4">
          <div>
            <h1 className="text-xl font-semibold tracking-tight">CuraLLM</h1>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              General health information with sources. Early-stage demo.
            </p>
          </div>
          <span className="shrink-0 rounded-full border border-amber-300 bg-amber-50 px-3 py-1 text-xs font-medium text-amber-800 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-200">
            Not for clinical use
          </span>
        </div>
      </header>

      <main className="flex flex-1 flex-col">
        <Chat />
      </main>

      <footer className="border-t border-slate-200 bg-white px-4 py-3 text-center text-xs text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400">
        CuraLLM shares general information only. It does not diagnose or recommend
        treatment. In an emergency, contact your local emergency services.
      </footer>
    </div>
  );
}
