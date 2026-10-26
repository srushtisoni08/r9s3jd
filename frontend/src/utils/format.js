const TZ = "Europe/London";

export const fmtTime = (iso) =>
  new Intl.DateTimeFormat("en-GB", {
    timeZone: TZ, hour: "2-digit", minute: "2-digit", hour12: false,
  }).format(new Date(iso));

export const fmtDateTime = (iso) =>
  iso
    ? new Intl.DateTimeFormat("en-GB", {
        timeZone: TZ, day: "2-digit", month: "short",
        hour: "2-digit", minute: "2-digit", hour12: false,
      }).format(new Date(iso))
    : "—";

export const fmtNum = (n, d = 0) =>
  n == null ? "—" : Number(n).toLocaleString("en-GB", { maximumFractionDigits: d });