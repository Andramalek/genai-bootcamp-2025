import { useState } from 'react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { useTheme } from "@/components/theme-provider";

export default function Settings() {
  const { theme, setTheme } = useTheme();
  const [resetConfirmation, setResetConfirmation] = useState("");

  const handleReset = () => {
    // Add reset logic here
    console.log("Resetting database...");
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label>Dark Mode</Label>
            <p className="text-sm text-muted-foreground">
              Toggle between light and dark theme
            </p>
          </div>
          <Switch
            checked={theme === "dark"}
            onCheckedChange={(checked) => setTheme(checked ? "dark" : "light")}
          />
        </div>

        <div className="space-y-4">
          <Label className="text-destructive text-lg">Danger Zone</Label>
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="destructive">Reset History</Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Are you sure?</AlertDialogTitle>
                <AlertDialogDescription>
                  This action cannot be undone. This will permanently delete all your study history
                  and progress data.
                  <div className="mt-4">
                    <Label htmlFor="reset-confirmation">
                      Type "reset me" to confirm:
                    </Label>
                    <Input
                      id="reset-confirmation"
                      value={resetConfirmation}
                      onChange={(e) => setResetConfirmation(e.target.value)}
                      className="mt-2"
                    />
                  </div>
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction
                  onClick={handleReset}
                  disabled={resetConfirmation !== "reset me"}
                  className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                >
                  Reset
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </div>
    </div>
  );
}