import React, { JSX } from "react";
import { Github, Twitter, Mail } from "lucide-react";

export default function Footer(): JSX.Element {
    const year = new Date().getFullYear();

    return (
        <footer className="w-full bg-background border-t border-border mt-[500px]">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
                <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-8">
                    <div className="flex items-center gap-3">
                        
                        <div className="text-sm text-muted-foreground">
                            Lightweight data visualizations built with care.
                        </div>
                    </div>


                <div className="mt-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                    <div className="text-sm text-muted-foreground">
                        © {year} MyApp. All rights reserved.
                    </div>

                    <div className="flex items-center space-x-4">
                        <a
                            href="https://github.com/your-org"
                            target="_blank"
                            rel="noopener noreferrer"
                            aria-label="GitHub"
                            className="text-muted-foreground hover:text-foreground"
                        >
                            <Github className="h-5 w-5" />
                        </a>

                        <a
                            href="https://twitter.com/your-handle"
                            target="_blank"
                            rel="noopener noreferrer"
                            aria-label="Twitter"
                            className="text-muted-foreground hover:text-foreground"
                        >
                            <Twitter className="h-5 w-5" />
                        </a>

                        <a
                            href="mailto:hello@yourdomain.com"
                            aria-label="Email"
                            className="text-muted-foreground hover:text-foreground"
                        >
                            <Mail className="h-5 w-5" />
                        </a>
                    </div>
                </div>
            </div>
            </div>
        </footer>
    );
}