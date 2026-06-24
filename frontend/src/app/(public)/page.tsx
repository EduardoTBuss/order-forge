import { redirect } from "next/navigation";
import { getSessionOrNull } from "@/auth/session";
import LoginButton from "@/auth/ui/LoginButton";
import AnimatedBackground from "@/components/AnimatedBackground";
import LanguageSelector from "@/components/LanguageSelector";
import ThemeToggle from "@/components/ThemeToggle";
import { getTranslator } from "@/i18n/server";

export default async function PublicHome() {
  const user = await getSessionOrNull();

  // If authenticated, redirect to private home
  if (user) {
    redirect("/home");
  }

  const [homeT, footerT, commonT] = await Promise.all([
    getTranslator("home"),
    getTranslator("footer"),
    getTranslator("common"),
  ]);

  // Show login screen for unauthenticated users
  return (
    <div className="relative isolate min-h-dvh w-full overflow-hidden bg-background">
      {/* Desktop layout - side by side */}
      <div className="hidden md:flex min-h-dvh">
        {/* Left side - Background image */}
        <div className="relative w-[65%] lg:w-[70%]">
          <div className="absolute inset-0 overflow-hidden">
            <AnimatedBackground className="absolute inset-0">
              <div
                className="absolute inset-0"
                style={{
                  backgroundImage: "url('/background.jpg')",
                  backgroundPosition: "center center",
                  backgroundSize: "cover",
                  backgroundRepeat: "no-repeat",
                }}
              />
              <div className="absolute inset-0 bg-gradient-to-r from-black/40 via-black/30 to-transparent" />
            </AnimatedBackground>
          </div>

          {/* Diagonal edge with shadow - outside overflow container */}
          <div
            className="absolute -right-32 top-0 h-full w-80 origin-top-right bg-background z-10"
            style={{
              transform: "skewX(-5deg)",
              boxShadow: "-12px 0 20px -4px rgba(0, 0, 0, 0.2)",
            }}
          />
        </div>

        {/* Right side - Content area */}
        <div className="relative z-10 flex w-[35%] lg:w-[30%] flex-col">
          <div className="flex items-center justify-end gap-1.5 p-6 animate-fade-in">
            <LanguageSelector />
            <ThemeToggle />
          </div>

          <section className="flex flex-1 flex-col justify-center -ml-8 lg:-ml-12 pr-10 lg:pr-12 pb-12">
            <div className="space-y-8">
              <div className="space-y-3 animate-fade-in-up">
                <h1 className="text-4xl lg:text-5xl font-extrabold leading-tight tracking-tight text-foreground">
                  <span className="block">{commonT("clientName")}</span>
                  <span className="block">{commonT("projectName")}</span>
                </h1>
                <p className="text-lg lg:text-xl text-muted-foreground leading-relaxed">
                  {homeT("hero.subheading")}
                </p>
              </div>
              <div className="animate-fade-in-up stagger-2">
                <LoginButton>{homeT("hero.loginCta")}</LoginButton>
              </div>
            </div>
          </section>

          <footer className="-ml-8 lg:-ml-12 pr-10 lg:pr-12 pb-6 text-xs text-muted-foreground animate-fade-in">
            {footerT("poweredBy")}
          </footer>
        </div>
      </div>

      {/* Mobile layout - stacked with image on top */}
      <div className="flex flex-col min-h-dvh md:hidden">
        {/* Top - Background image with diagonal bottom edge */}
        <div className="relative h-[55vh] min-h-[240px] overflow-hidden">
          <AnimatedBackground className="absolute inset-0">
            <div
              className="absolute inset-0"
              style={{
                backgroundImage: "url('/background.jpg')",
                backgroundPosition: "center center",
                backgroundSize: "cover",
                backgroundRepeat: "no-repeat",
              }}
            />
            <div className="absolute inset-0 bg-gradient-to-b from-black/30 via-black/20 to-transparent" />
          </AnimatedBackground>

          {/* Language/Theme controls overlay */}
          <div className="absolute top-0 right-0 flex items-center gap-1.5 p-4 z-10">
            <LanguageSelector variant="outlined" />
            <ThemeToggle variant="outlined" />
          </div>

          {/* Diagonal bottom edge */}
          <div
            className="absolute -bottom-px -left-4 -right-1 h-14 bg-background z-10"
            style={{ clipPath: "polygon(0 100%, 100% 0, 100% 100%)" }}
          />
        </div>

        {/* Bottom - Content area */}
        <div className="relative flex-1 flex flex-col bg-background px-6 pb-6">
          <section className="flex-1 flex flex-col justify-center">
            <div className="space-y-6 text-right">
              <div className="space-y-3 animate-fade-in-up">
                <h1 className="text-3xl sm:text-4xl font-extrabold leading-tight tracking-tight text-foreground">
                  {commonT("projectName")} - {commonT("clientName")}
                </h1>
                <p className="text-base sm:text-lg text-muted-foreground leading-relaxed">
                  {homeT("hero.subheading")}
                </p>
              </div>
              <div className="animate-fade-in-up stagger-2">
                <LoginButton>{homeT("hero.loginCta")}</LoginButton>
              </div>
            </div>
          </section>

          <footer className="pt-6 text-xs text-muted-foreground text-right animate-fade-in">
            {footerT("poweredBy")}
          </footer>
        </div>
      </div>
    </div>
  );
}
